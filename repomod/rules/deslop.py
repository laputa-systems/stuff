"""Hardening for Rust repositories whose deslop pass reached the Tests step.

`make-coverage-target`, `mutants-diff-lane`, and `strict-typing-profile` apply
only to non-fork repositories (or forks tagged `fork-diverged`) with a root
Cargo.toml, and only once the Tests step is closed (`TODO-DESLOP.md` without an
open DSLP-4 ticket) or the mutation or coverage target is already present.
Python and TypeScript lanes follow STUF-83. `mutants-diff-lane` has a fixer
that writes the reference mutation gate; `fleet/policy/rust-tools.toml` pins
the cargo-mutants version the lane installs. `fleet/policy/retention.toml`
owns the read-only guarantees for repositories that already opted in.
"""

from __future__ import annotations

import dataclasses
import re
import tomllib
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from repomod import paths
from repomod.git import GitError
from repomod.rules.actions import load_pins
from repomod.rules.ci_workflow import _make_command, _trigger_problem
from repomod.rules.consistency import _declared_make_targets
from repomod.rules.retention import _mutation, _strict, _targets
from repomod.rules.workflows import read_workflow_sources
from repomod.types import Finding, Repository, Rule, TagPredicate, operational, violation

_POLICY = 'fleet/policy/rust-tools.toml'
_FIXERS = Path(__file__).resolve().parent.parent / 'fixers'


def _covered(repository: Repository) -> bool:
    tags = set(repository.tags)
    return 'fork' not in tags or 'fork-diverged' in tags


def _tests_closed(root: Path) -> bool:
    try:
        text = (root / 'TODO-DESLOP.md').read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        return False
    return re.search(r'^### DSLP-4 ·', text, re.MULTILINE) is None


def _has_target(root: Path, target: str) -> bool:
    path = root / 'Makefile'
    try:
        if not path.is_file():
            return False
        source = path.read_text(encoding='utf-8')
        declared = _declared_make_targets(path)
    except (OSError, UnicodeError):
        return False
    if declared is None or target not in declared:
        return False
    rules = (line.partition(':')[0].split() for line in source.splitlines()
             if line and not line[0].isspace() and ':' in line and not line.startswith('#'))
    return any(target in names and '.PHONY' not in names for names in rules)


def _eligible(root: Path, repository: Repository) -> bool:
    if not _covered(repository) or not (root / 'Cargo.toml').is_file():
        return False
    return _tests_closed(root) or _has_target(root, 'coverage') or _has_target(root, 'mutants-diff')


def _tool_pin(name: str) -> str:
    path = paths.POLICY / 'rust-tools.toml'
    if path.is_symlink():
        raise ValueError('rust-tools policy is a symlink')
    try:
        data = tomllib.loads(path.read_text(encoding='utf-8'))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f'cannot load rust-tools policy: {error}') from error
    if set(data) != {'tools'} or not isinstance(data['tools'], dict):
        raise ValueError('unknown or missing rust-tools policy, or invalid tools table')
    value = data['tools'].get(name)
    if not isinstance(value, str) or not re.fullmatch(r'\d+\.\d+\.\d+', value):
        raise ValueError(f'invalid {name} pin in rust-tools policy')
    return value


def _coverage_target(root: Path, repository: Repository) -> list[Finding]:
    if not _eligible(root, repository):
        return []
    return _targets(root, repository, 'make-coverage-target', 'coverage')


def _pr_workflow_mutants_job(root: Path) -> tuple[bool, bool] | None:
    try:
        sources, _problems = read_workflow_sources(root)
    except OSError:
        return None
    found_workflow = False
    found_job = False
    for _path, source in sources:
        try:
            doc = YAML(typ='safe').load(source)
        except YAMLError:
            continue
        if not isinstance(doc, dict):
            continue
        pull_request, trigger_problem = _trigger_problem(doc, root)
        if not pull_request or trigger_problem is not None:
            continue
        found_workflow = True
        jobs = doc.get('jobs')
        if isinstance(jobs, dict) and 'mutants' in jobs:
            found_job = True
    return found_workflow, found_job


def _base_ref_findings(root: Path, repository: Repository) -> list[Finding]:
    try:
        sources, _ = read_workflow_sources(root)
    except OSError:
        return []
    findings = []
    for path, source in sources:
        try:
            doc = YAML(typ='safe').load(source)
        except YAMLError:
            continue
        if not isinstance(doc, dict):
            continue
        pull_request, trigger_problem = _trigger_problem(doc, root)
        if not pull_request or trigger_problem is not None:
            continue
        jobs = doc.get('jobs')
        if not isinstance(jobs, dict):
            continue
        job = jobs.get('mutants')
        if not isinstance(job, dict):
            continue
        raw_steps = job.get('steps')
        steps = [step for step in raw_steps if isinstance(step, dict)] if isinstance(raw_steps, list) else []
        target = frozenset({'mutants-diff'})
        command_step = next(
            (step for step in steps
             if isinstance(step.get('run'), str) and _make_command(step['run'], target)),
            None,
        )
        if command_step is None:
            continue
        env = None
        for layer in (command_step, job):
            layer_env = layer.get('env')
            if isinstance(layer_env, dict):
                env = layer_env
                break
        base_ref = env.get('BASE_REF') if env is not None else None
        if not (isinstance(base_ref, str) and 'github.base_ref' in base_ref):
            findings.append(violation(
                repository,
                'mutants-diff-lane',
                path,
                'mutants-diff job step must pass BASE_REF through env (github.base_ref)',
            ))
    return findings


def _mutants_diff_lane(root: Path, repository: Repository) -> list[Finding]:
    if not _eligible(root, repository):
        return []
    try:
        pin = _tool_pin('cargo-mutants')
    except ValueError as error:
        return [operational(repository, 'mutants-diff-lane', _POLICY, str(error))]
    fixable_job = False
    lane = _pr_workflow_mutants_job(root)
    if lane is not None:
        found_workflow, found_job = lane
        fixable_job = found_workflow and not found_job
    findings = _targets(root, repository, 'mutants-diff-lane', 'mutants-diff')
    job_findings = _mutation(root, repository, 'mutants-diff-lane', pin=pin)
    marked = [dataclasses.replace(finding, fixable=True) for finding in findings]
    if job_findings:
        marked.extend(
            dataclasses.replace(finding, fixable=fixable_job) for finding in job_findings
        )
    marked.extend(_base_ref_findings(root, repository))
    return marked


_STRICT_PYTHON = [
    'ty.missing-type-argument=error',
    'ty.unsound-return-statement=error',
    'ty.unused-ignore-comment=error',
    'ruff.ANN401=selected',
]


def _strict_typing_profile(root: Path, repository: Repository) -> list[Finding]:
    if not _eligible(root, repository):
        return []
    settings = ['rust.unsafe_code=forbid']
    if (root / 'pyproject.toml').is_file():
        settings = [*settings, *_STRICT_PYTHON]
    return _strict(root, repository, settings, 'strict-typing-profile')


def _gate_source(name: str) -> str:
    try:
        return (_FIXERS / name).read_text(encoding='utf-8')
    except (OSError, UnicodeError) as error:
        raise ValueError(f'mutants gate template {name} unreadable: {error}') from error


_GATE_TOML = (
    'scope = ["src/"]\n'
    'irrelevant = ["*.md", "LICENSE", "LICENSE.*"]\n'
    'budget_seconds = 900\n'
    'timeout_seconds = 10\n'
    'build_timeout_seconds = 300\n'
    'jobs = 4\n'
)

_MAKEFILE_BLOCK = (
    '\nBASE ?= origin/main\n'
    '\n'
    '.PHONY: mutants-selftest mutants-diff\n'
    'mutants-selftest:\n'
    "\tpython3 -B -m unittest discover -s scripts -p 'test_mutants_gate.py'\n"
    '\n'
    'mutants-diff: mutants-selftest\n'
    '\tpython3 -B scripts/mutants_gate.py "$(BASE)"\n'
)


def _mutants_job(checkout_sha: str, checkout_version: str, install_sha: str, install_version: str, pin: str) -> str:
    return (
        '  mutants:\n'
        '    name: mutants\n'
        '    runs-on: ubuntu-26.04-arm\n'
        '    permissions:\n'
        '      contents: read\n'
        '    steps:\n'
        f'      - uses: actions/checkout@{checkout_sha} # {checkout_version}\n'
        '        with:\n'
        '          persist-credentials: false\n'
        '          fetch-depth: 0\n'
        f'      - uses: taiki-e/install-action@{install_sha} # {install_version}\n'
        '        with:\n'
        f'          tool: cargo-mutants@{pin}\n'
        '      - name: mutants\n'
        '        env:\n'
        '          BASE_REF: ${{ github.base_ref }}\n'
        '        run: make mutants-diff BASE="origin/$BASE_REF"\n'
    )


def _insert_job(source: str, job: str) -> str | None:
    try:
        doc = YAML(typ='safe').load(source)
    except YAMLError:
        return None
    jobs = doc.get('jobs') if isinstance(doc, dict) else None
    if not isinstance(jobs, dict) or 'mutants' in jobs:
        return None
    source = re.sub(r'(?m)^jobs:[ \t]*\{\s*\}[ \t]*$', 'jobs:', source)
    lines = source.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if re.fullmatch(r'jobs:[ \t]*(#.*)?\n?', line):
            lines.insert(index + 1, job)
            return ''.join(lines)
    return None


def _mutants_fix(root: Path, repository: Repository) -> dict[str, str]:
    lane = _pr_workflow_mutants_job(root)
    try:
        pin = _tool_pin('cargo-mutants')
    except ValueError as error:
        raise GitError(str(error)) from error
    plan: dict[str, str] = {}
    for name in ('mutants_gate.py', 'test_mutants_gate.py'):
        target = root / 'scripts' / name
        if not target.exists():
            plan[f'scripts/{name}'] = _gate_source(name)
    if not (root / '.cargo' / 'mutants-gate.toml').exists():
        plan['.cargo/mutants-gate.toml'] = _GATE_TOML
    makefile = root / 'Makefile'
    if not _has_target(root, 'mutants-diff'):
        try:
            existing = makefile.read_text(encoding='utf-8') if makefile.is_file() else ''
        except (OSError, UnicodeError) as error:
            raise GitError(f'cannot read Makefile: {error}') from error
        plan['Makefile'] = existing.rstrip('\n') + ('\n' if existing else '') + _MAKEFILE_BLOCK
    if lane is None or not lane[0] or lane[1]:
        return plan
    sources, problems = read_workflow_sources(root)
    if problems:
        raise GitError('; '.join(f'{path}: {message}' for path, message in problems))
    pins = load_pins()
    checkout, install = pins.get('actions/checkout'), pins.get('taiki-e/install-action')
    if checkout is None or install is None:
        raise GitError('actions.toml is missing the actions/checkout or taiki-e/install-action pin')
    jobs = _mutants_job(checkout.sha, checkout.version, install.sha, install.version, pin)
    for path, source in sources:
        try:
            doc = YAML(typ='safe').load(source)
        except YAMLError:
            continue
        if not isinstance(doc, dict):
            continue
        pull_request, trigger_problem = _trigger_problem(doc, root)
        if not pull_request or trigger_problem is not None:
            continue
        fixed = _insert_job(source, jobs)
        if fixed is None:
            raise GitError(f'cannot insert the mutants job into {path}')
        plan[path] = fixed
        return plan
    raise GitError('cannot determine the pull_request workflow to hold the mutants job')


def deslop_rules() -> tuple[Rule, ...]:
    from repomod.rules.actions import _validate_workflows

    return (
        Rule(
            'make-coverage-target',
            'Require a coverage make target in hardened Rust repositories',
            TagPredicate(),
            _coverage_target,
            None,
            None,
            (),
        ),
        Rule(
            'mutants-diff-lane',
            'Require the pull_request mutants-diff lane pinned to the approved cargo-mutants',
            TagPredicate(),
            _mutants_diff_lane,
            _mutants_fix,
            'ci(deslop): add the mutants-diff lane',
            (
                'Makefile',
                '.github/workflows/*.yml',
                '.github/workflows/*.yaml',
                'scripts/mutants_gate.py',
                'scripts/test_mutants_gate.py',
                '.cargo/mutants-gate.toml',
            ),
            _validate_workflows,
        ),
        Rule(
            'strict-typing-profile',
            'Require the fleet-wide strict typing settings where the deslop pass adopted them',
            TagPredicate(),
            _strict_typing_profile,
            None,
            None,
            (),
        ),
    )
