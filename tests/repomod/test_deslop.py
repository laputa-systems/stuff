from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
from ruamel.yaml import YAML

from repomod.git import GitError
from repomod.rules import deslop, retention
from repomod.types import RepoId, Repository

CARGO = '[lints.rust]\nunsafe_code = "forbid"\n'
TODO_CLOSED = '# TODO-DESLOP\n\n## Tickets\n\n### DSLP-5 · P3 · Dead code\n'
WORKFLOW_MUTANTS = (
    'on: pull_request\n'
    'jobs:\n'
    '  build:\n'
    '    runs-on: ubuntu-latest\n'
    '    steps:\n'
    '      - run: make test\n'
    '  mutants:\n'
    '    name: mutants\n'
    '    runs-on: ubuntu-26.04-arm\n'
    '    permissions:\n'
    '      contents: read\n'
    '    steps:\n'
    '      - uses: actions/checkout@' + 'a' * 40 + '\n'
    '        with:\n'
    '          persist-credentials: false\n'
    '          fetch-depth: 0\n'
    '      - uses: taiki-e/install-action@' + 'b' * 40 + '\n'
    '        with:\n'
    '          tool: cargo-mutants@27.1.0\n'
    '      - run: make mutants-diff BASE="origin/$BASE_REF"\n'
    '        env:\n'
    '          BASE_REF: ${{ github.base_ref }}\n'
)
GATE_CONFIG = (
    'scope = ["src/lib.rs"]\n'
    "critical = ' in (parse|admit)\\b'\n"
    'irrelevant = ["*.md"]\n'
)
MAKEFILE = (
    '.PHONY: build test coverage mutants-diff mutants-selftest\n'
    'coverage:\n\ttrue\n'
    'mutants-diff:\n\ttrue\n'
    'mutants-selftest:\n\ttrue\n'
)


def _register(monkeypatch: pytest.MonkeyPatch, repo: Repository, *, registered: bool = True) -> None:
    names = [str(repo.id)] if registered else []
    monkeypatch.setattr(deslop, '_tool_pin', lambda name: '27.1.0')
    monkeypatch.setattr(retention, '_policy', lambda: {
        'mutation-lane': {'repositories': names},
        'coverage-target': {'repositories': names},
        'strict-profile': {str(repo.id): {'settings': ['rust.unsafe_code=forbid']}},
    })


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Repository]:
    repo = Repository(RepoId('laputa-systems', 'fakecrate'), ('tool', 'rust'))
    _register(monkeypatch, repo)
    (tmp_path / 'Cargo.toml').write_text(CARGO)
    (tmp_path / 'TODO-DESLOP.md').write_text(TODO_CLOSED)
    (tmp_path / 'Makefile').write_text(MAKEFILE)
    (tmp_path / '.cargo').mkdir()
    (tmp_path / '.cargo/mutants-gate.toml').write_text(GATE_CONFIG)
    workflows = tmp_path / '.github/workflows'
    workflows.mkdir(parents=True)
    (workflows / 'ci.yml').write_text(WORKFLOW_MUTANTS)
    return tmp_path, repo


def test_hardened_repository_is_clean(project: tuple[Path, Repository]) -> None:
    root, repo = project
    assert deslop._coverage_target(root, repo) == []
    assert deslop._mutants_diff_lane(root, repo) == []
    assert deslop._strict_typing_profile(root, repo) == []


def test_campaign_state_does_not_select_the_lane(
    project: tuple[Path, Repository], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, repo = project
    _register(monkeypatch, repo, registered=False)
    (root / 'Makefile').write_text('test:\n\ttrue\n')
    (root / '.github/workflows/ci.yml').unlink()
    (root / '.cargo/mutants-gate.toml').unlink()
    for state in (TODO_CLOSED, '## Tickets\n\n### DSLP-4 · P2 · Tests\n'):
        (root / 'TODO-DESLOP.md').write_text(state)
        assert deslop._coverage_target(root, repo) == []
        assert deslop._mutants_diff_lane(root, repo) == []


def test_adopted_targets_do_not_select_an_unregistered_repository(
    project: tuple[Path, Repository], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, repo = project
    _register(monkeypatch, repo, registered=False)
    (root / '.cargo/mutants-gate.toml').unlink()
    (root / 'TODO-DESLOP.md').unlink()
    assert deslop._coverage_target(root, repo) == []
    assert deslop._mutants_diff_lane(root, repo) == []


def test_registration_survives_deleting_the_repository_evidence(project: tuple[Path, Repository]) -> None:
    root, repo = project
    (root / 'TODO-DESLOP.md').unlink()
    (root / 'Makefile').write_text('test:\n\ttrue\n')
    assert any('missing coverage target' in f.message for f in deslop._coverage_target(root, repo))
    assert any('missing mutants-diff target' in f.message for f in deslop._mutants_diff_lane(root, repo))


def test_plain_fork_is_not_eligible(project: tuple[Path, Repository]) -> None:
    root, _ = project
    repo = Repository(RepoId('laputa-systems', 'fakecrate'), ('tool', 'rust', 'fork'))
    (root / 'Makefile').write_text('test:\n\ttrue\n')
    assert deslop._coverage_target(root, repo) == []
    fork_diverged = Repository(RepoId('laputa-systems', 'fakecrate'), ('tool', 'rust', 'fork', 'fork-diverged'))
    assert any('coverage' in finding.message for finding in deslop._coverage_target(root, fork_diverged))


def test_non_rust_repository_is_skipped(project: tuple[Path, Repository]) -> None:
    root, repo = project
    (root / 'Cargo.toml').unlink()
    (root / 'Makefile').write_text('test:\n\ttrue\n')
    assert deslop._coverage_target(root, repo) == []
    assert deslop._mutants_diff_lane(root, repo) == []
    assert deslop._strict_typing_profile(root, repo) == []


def test_missing_coverage_target_is_reported(project: tuple[Path, Repository]) -> None:
    root, repo = project
    (root / 'Makefile').write_text('.PHONY: test\nmutants-diff:\n\ttrue\nmutants-selftest:\n\ttrue\n')
    findings = deslop._coverage_target(root, repo)
    assert any('missing coverage target' in finding.message for finding in findings)


def test_missing_mutants_target_is_reported(project: tuple[Path, Repository]) -> None:
    root, repo = project
    (root / 'Makefile').write_text('coverage:\n\ttrue\n')
    findings = deslop._mutants_diff_lane(root, repo)
    assert any('missing mutants-diff target' in finding.message for finding in findings)


def test_wrong_cargo_mutants_pin_is_reported(project: tuple[Path, Repository]) -> None:
    root, repo = project
    workflow = root / '.github/workflows/ci.yml'
    workflow.write_text(workflow.read_text().replace('cargo-mutants@27.1.0', 'cargo-mutants@27.0.0'))
    findings = deslop._mutants_diff_lane(root, repo)
    assert any('cargo-mutants pinned at 27.1.0' in finding.message for finding in findings)


def test_mutants_job_requires_base_ref_env(project: tuple[Path, Repository]) -> None:
    root, repo = project
    workflow = root / '.github/workflows/ci.yml'
    text = workflow.read_text()
    text = text.replace('        env:\n          BASE_REF: ${{ github.base_ref }}\n', '')
    workflow.write_text(text)
    assert any('mutants-diff job' in finding.message for finding in deslop._mutants_diff_lane(root, repo))


def test_missing_strict_rust_setting_is_reported(project: tuple[Path, Repository]) -> None:
    root, repo = project
    (root / 'Cargo.toml').write_text('[lints.rust]\nunsafe_code = "warn"\n')
    findings = deslop._strict_typing_profile(root, repo)
    assert any('rust.unsafe_code=forbid' in finding.message for finding in findings)


def test_unregistered_profile_is_not_inferred_from_files(project: tuple[Path, Repository]) -> None:
    root, _ = project
    repo = Repository(RepoId('laputa-systems', 'terminal'), ('tool', 'rust', 'python'))
    (root / 'Cargo.toml').write_text('[lints.rust]\nunsafe_code = "warn"\n')
    (root / 'pyproject.toml').write_text('[tool.ty.rules]\n')
    assert deslop._strict_typing_profile(root, repo) == []


def test_only_adopted_python_setting_is_required(
    project: tuple[Path, Repository], monkeypatch: pytest.MonkeyPatch
) -> None:
    root, repo = project
    setting = 'ty.missing-type-argument=error'
    monkeypatch.setattr(retention, '_policy', lambda: {
        'strict-profile': {str(repo.id): {'settings': [setting]}},
    })
    (root / 'Cargo.toml').write_text('[lints.rust]\nunsafe_code = "warn"\n')
    findings = deslop._strict_typing_profile(root, repo)
    assert [finding.message for finding in findings] == [f'missing strict setting {setting}']


def _apply_plan(root: Path, plan: dict[str, str]) -> None:
    for relative, content in plan.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def test_fixer_writes_the_reference_gate(project: tuple[Path, Repository]) -> None:
    root, repo = project
    (root / '.cargo/mutants-gate.toml').unlink()
    (root / 'Makefile').write_text('.PHONY: build test\ntest:\n\ttrue\n')
    (root / '.github/workflows/ci.yml').write_text(
        'on: pull_request\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - run: make test\n'
    )
    plan = deslop._mutants_fix(root, repo)
    assert set(plan) == {
        'scripts/mutants_gate.py',
        'scripts/test_mutants_gate.py',
        'Makefile',
        '.github/workflows/ci.yml',
    }
    _apply_plan(root, plan)
    assert not (root / '.cargo/mutants-gate.toml').exists()
    text = (root / 'Makefile').read_text(encoding='utf-8')
    assert 'mutants-diff: mutants-selftest' in text
    assert '\tbash -lc "true"' not in text
    workflow = YAML(typ='safe').load((root / '.github/workflows/ci.yml').read_text(encoding='utf-8'))
    job = workflow['jobs']['mutants']
    assert job['name'] == 'mutants'
    steps = job['steps']
    assert steps[1]['with']['tool'] == 'cargo-mutants@27.1.0'
    assert steps[2]['env']['BASE_REF'] == '${{ github.base_ref }}'
    subprocess.run(
        ['python3', '-m', 'py_compile', str(root / 'scripts/mutants_gate.py'),
         str(root / 'scripts/test_mutants_gate.py')],
        check=True,
    )
    findings = deslop._mutants_diff_lane(root, repo)
    assert [(f.file, f.fixable) for f in findings] == [('.cargo/mutants-gate.toml', False)]
    assert 'critical' in findings[0].message
    (root / '.cargo/mutants-gate.toml').parent.mkdir(exist_ok=True)
    (root / '.cargo/mutants-gate.toml').write_text(GATE_CONFIG)
    assert deslop._mutants_diff_lane(root, repo) == []


def test_missing_or_defaulted_scope_declaration_is_a_non_fixable_finding(project: tuple[Path, Repository]) -> None:
    root, repo = project
    config = root / '.cargo/mutants-gate.toml'
    for text in (None, 'scope = ["src/"]\nirrelevant = []\n', 'critical = "x"\nirrelevant = []\n',
                 'scope = ["src/"]\ncritical = "x"\nirrelevant = []\n', '{'):
        if text is None:
            config.unlink()
        else:
            config.write_text(text)
        findings = deslop._mutants_diff_lane(root, repo)
        assert [(f.file, f.fixable, f.kind) for f in findings] == [('.cargo/mutants-gate.toml', False, 'violation')]
        assert 'declare the required mutation scope' in findings[0].message


def test_gate_template_selftest_passes() -> None:
    fixers = Path(deslop.__file__).resolve().parent.parent / 'fixers'
    result = subprocess.run(
        [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(fixers), '-p', 'test_mutants_gate.py'],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr


def test_fixer_preserves_existing_gate(project: tuple[Path, Repository]) -> None:
    root, repo = project
    gate = root / 'scripts' / 'mutants_gate.py'
    gate.parent.mkdir(exist_ok=True)
    gate.write_text('# custom gate\n')
    (root / 'Makefile').write_text('test:\n\ttrue\n')
    (root / '.github/workflows/ci.yml').write_text('on: pull_request\njobs: {}\n')
    plan = deslop._mutants_fix(root, repo)
    assert 'scripts/mutants_gate.py' not in plan
    _apply_plan(root, plan)
    assert gate.read_text(encoding='utf-8') == '# custom gate\n'


def test_fixer_without_dispatchable_workflow_keeps_tooling_partial(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = Repository(RepoId('laputa-systems', 'fakecrate'), ('tool', 'rust'))
    _register(monkeypatch, repo)
    (tmp_path / 'Cargo.toml').write_text(CARGO)
    (tmp_path / 'Makefile').write_text('test:\n\ttrue\n')
    plan = deslop._mutants_fix(tmp_path, repo)
    assert '.github/workflows/ci.yml' not in plan
    assert 'Makefile' in plan


def test_fixer_aborts_when_workflow_has_no_jobs_mapping(project: tuple[Path, Repository]) -> None:
    root, repo = project
    (root / 'Makefile').write_text('test:\n\ttrue\n')
    (root / '.github/workflows/ci.yml').write_text('on: pull_request\npermissions: {}\n')
    with pytest.raises(GitError):
        deslop._mutants_fix(root, repo)


def test_fixable_flags_follow_job_presence(project: tuple[Path, Repository]) -> None:
    root, repo = project
    findings = deslop._mutants_diff_lane(root, repo)
    assert findings == []
    workflow = root / '.github/workflows/ci.yml'
    text = workflow.read_text()
    checkout = '        with:\n          persist-credentials: false\n          fetch-depth: 0\n'
    text = text.replace(checkout, '        if: false\n' + checkout)
    workflow.write_text(text)
    findings = deslop._mutants_diff_lane(root, repo)
    assert any(not finding.fixable for finding in findings)


def test_tool_pin_loads_and_validates_real_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for content, message in [
        ('[tools]\ncargo-mutants = "27.1.0"\n', None),
        ('[tools]\ncargo-mutants = "latest"\n', 'invalid cargo-mutants pin'),
        ('[unrelated]\n', 'unknown or missing rust-tools policy'),
    ]:
        policy = tmp_path / 'policy'
        policy.mkdir(exist_ok=True)
        (policy / 'rust-tools.toml').write_text(content)
        monkeypatch.setattr(deslop.paths, 'POLICY', policy)
        if message is None:
            assert deslop._tool_pin('cargo-mutants') == '27.1.0'
        else:
            with pytest.raises(ValueError, match=re.escape(message)):
                deslop._tool_pin('cargo-mutants')
