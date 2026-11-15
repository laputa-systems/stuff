from __future__ import annotations

from pathlib import Path

import pytest

from repomod.rules import retention
from repomod.types import RepoId, Repository


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Repository]:
    repo = Repository(RepoId('laputa-systems', 'srv'), ('tool', 'rust'))
    policy = {
        'mutation-lane': {'repositories': [str(repo.id)]},
        'coverage-target': {'repositories': [str(repo.id)]},
        'strict-profile': {str(repo.id): {'settings': ['rust.unsafe_code=forbid']}},
    }
    monkeypatch.setattr(retention, '_policy', lambda: policy)
    (tmp_path / 'Makefile').write_text('mutants-diff:\n\ttrue\ncoverage:\n\ttrue\n')
    (tmp_path / 'Cargo.toml').write_text('[lints.rust]\nunsafe_code = "forbid"\n')
    (tmp_path / 'TODO-DESLOP.md').write_text('tests complete\n')
    workflows = tmp_path / '.github/workflows'
    workflows.mkdir(parents=True)
    (workflows / 'ci.yml').write_text(
        'on: pull_request\njobs:\n  mutants:\n    runs-on: ubuntu-latest\n    steps:\n'
        '      - uses: actions/checkout@' + 'a' * 40 + '\n'
        '        with:\n          fetch-depth: 0\n'
        '      - uses: taiki-e/install-action@' + 'b' * 40 + '\n'
        '        with:\n          tool: cargo-mutants@27.1.0\n'
        '      - run: make mutants-diff BASE="origin/$BASE_REF"\n'
    )
    return tmp_path, repo


def test_removing_repository_files_does_not_remove_retention(project: tuple[Path, Repository]) -> None:
    root, repo = project
    for rule in ('mutation-lane', 'coverage-target', 'strict-profile'):
        assert retention._check(root, repo, rule) == []
    (root / 'TODO-DESLOP.md').unlink()
    for rule in ('mutation-lane', 'coverage-target', 'strict-profile'):
        assert retention._check(root, repo, rule) == []


@pytest.mark.parametrize(('change', 'rule', 'message'), [
    ('target', 'mutation-lane', 'missing mutants-diff target'),
    ('job', 'mutation-lane', 'missing supported pull_request mutants-diff job'),
    ('if', 'mutation-lane', 'missing supported pull_request mutants-diff job'),
    ('continue', 'mutation-lane', 'missing supported pull_request mutants-diff job'),
    ('setup-if', 'mutation-lane', 'missing supported pull_request mutants-diff job'),
    ('setup-late', 'mutation-lane', 'missing supported pull_request mutants-diff job'),
    ('coverage', 'coverage-target', 'missing coverage target'),
    ('strict', 'strict-profile', 'rust.unsafe_code=forbid'),
])
def test_removal_is_reported(
    project: tuple[Path, Repository], change: str, rule: str, message: str
) -> None:
    root, repo = project
    workflow = root / '.github/workflows/ci.yml'
    if change == 'target':
        (root / 'Makefile').write_text('.PHONY: mutants-diff coverage\ncoverage:\n\ttrue\n')
    elif change == 'job':
        workflow.write_text('on: pull_request\njobs: {}\n')
    elif change in {'if', 'continue'}:
        key = 'if: false' if change == 'if' else 'continue-on-error: true'
        workflow.write_text(workflow.read_text().replace(
            '      - run: make mutants-diff', f'      - {key}\n        run: make mutants-diff'
        ))
    elif change == 'setup-if':
        workflow.write_text(workflow.read_text().replace(
            '        with:\n          fetch-depth', '        if: false\n        with:\n          fetch-depth'
        ))
    elif change == 'setup-late':
        source = workflow.read_text()
        command = '      - run: make mutants-diff BASE="origin/$BASE_REF"\n'
        workflow.write_text(source.replace(command, '').replace('    steps:\n', '    steps:\n' + command))
    elif change == 'coverage':
        (root / 'Makefile').write_text('mutants-diff:\n\ttrue\n')
    else:
        (root / 'Cargo.toml').write_text('[lints.rust]\nunsafe_code = "warn"\n')
    findings = retention._check(root, repo, rule)
    assert any(message in finding.message for finding in findings), findings


def test_unlisted_repository_is_skipped(project: tuple[Path, Repository]) -> None:
    root, _ = project
    repo = Repository(RepoId('acme', 'other'), ('tool',))
    for rule in ('mutation-lane', 'coverage-target', 'strict-profile'):
        assert retention._check(root, repo, rule) == []


@pytest.mark.parametrize(('bad', 'message'), [
    ('[unknown]\nrepositories = []\n', 'unknown or missing retention guarantee'),
    ('[mutation-lane]\nrepositories = ["missing/repo"]\n', 'outside the catalog'),
    ('[strict-profile."laputa-systems/srv"]\nsettings = ["unknown=error"]\n', 'unknown strict-profile setting'),
])
def test_invalid_policy_is_operational(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bad: str, message: str
) -> None:
    from repomod import paths

    monkeypatch.setattr(paths, 'POLICY', tmp_path)
    sections = {
        'mutation-lane': '[mutation-lane]\nrepositories = []\n',
        'coverage-target': '[coverage-target]\nrepositories = []\n',
        'strict-profile': '[strict-profile]\n',
    }
    key = bad.split(']')[0].split('.')[0].lstrip('[')
    sections[key] = bad
    (tmp_path / 'retention.toml').write_text('version = 1\n' + ''.join(sections.values()))
    repo = Repository(RepoId('laputa-systems', 'srv'), ('tool',))
    findings = retention._check(tmp_path, repo, 'mutation-lane')
    assert len(findings) == 1
    assert findings[0].kind == 'operational'
    assert message in findings[0].message
