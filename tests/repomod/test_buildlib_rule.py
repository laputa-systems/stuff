from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from repomod.rules import buildlib
from repomod.rules import rules as registered_rules
from repomod.types import RepoId, Repository

WHEEL = 'laputa_buildlib-0.2.0-py3-none-any.whl'
WHEEL_SHA = 'aaee620f0478544b1d32075b44de48e69bbcbd8b974d5f599d037494d59f4b4a'
OTHER_SHA = '0' * 64
SHIM = b'#!/bin/sh\nexec python3 "$@"\n'
LOCK = b'release test\n'
REPO = 'joshuarli/pi-build'


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _toml_list(items: tuple[str, ...]) -> str:
    return '[' + ', '.join(f'"{item}"' for item in items) + ']'


def _policy_text(*, enrolled: str = '', assess: tuple[str, ...] = (), exempt: str = '') -> str:
    text = (
        'version = 1\n\n'
        '[artifact]\n'
        'wheel_version = "0.2.0"\n'
        f'wheel_filename = "{WHEEL}"\n'
        f'wheel_sha256 = "{WHEEL_SHA}"\n\n'
        '[artifact.bootstrap_sha256]\n'
        f'"buildlib-run" = "{_sha(SHIM)}"\n'
        f'"python.lock" = "{_sha(LOCK)}"\n'
    )
    for name in assess:
        text += f'\n[assess."{name}"]\n'
    return text + enrolled + exempt


def _enrolled_text(
    *,
    name: str = REPO,
    entrypoints: tuple[str, ...] = ('scripts/build.py',),
    bootstrap: bool = True,
    local: dict[str, str] | None = None,
) -> str:
    text = (
        f'\n[enrolled."{name}"]\n'
        f'entrypoints = {_toml_list(entrypoints)}\n'
        f'bootstrap = {str(bootstrap).lower()}\n'
    )
    if local is not None:
        text += f'\n[enrolled."{name}".bootstrap_sha256]\n'
        for shim, digest in local.items():
            text += f'"{shim}" = "{digest}"\n'
    return text


def _exempt_text(name: str = REPO, *, reason: str | None = 'Native tooling sufficient.',
                 reassess: str | None = 'Reassess if packaging appears.') -> str:
    text = f'\n[exempt."{name}"]\n'
    if reason is not None:
        text += f'reason = "{reason}"\n'
    if reassess is not None:
        text += f'reassess = "{reassess}"\n'
    return text


def _pyproject(dependencies: tuple[str, ...] = ('laputa-buildlib==0.2.0',)) -> str:
    return (
        '[project]\n'
        'name = "fake"\n'
        'version = "0.1.0"\n'
        'requires-python = ">=3.15"\n'
        f'dependencies = {_toml_list(dependencies)}\n'
    )


def _uv_lock(digest: str = WHEEL_SHA) -> str:
    return (
        'version = 1\n'
        'revision = 3\n'
        'requires-python = ">=3.15"\n\n'
        '[[package]]\n'
        'name = "laputa-buildlib"\n'
        'version = "0.2.0"\n'
        f'wheels = [{{ url = "https://pypi.example/{WHEEL}", hash = "sha256:{digest}", size = 1 }}]\n'
    )


def _sources(digest: str = WHEEL_SHA) -> str:
    return json.dumps({
        'schema_version': 1,
        'inputs': [{
            'name': 'laputa-buildlib',
            'version': '0.2.0',
            'sha256': digest,
            'url': f'https://pypi.example/{WHEEL}',
        }],
    })


def _write_policy(policy: Path, text: str) -> None:
    (policy / 'buildlib.toml').write_text(text, encoding='utf-8')


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Repository, Path]:
    repository = Repository(RepoId.parse(REPO), ('build', 'python'))
    policy = tmp_path / 'policy'
    policy.mkdir()
    monkeypatch.setattr(buildlib.paths, 'POLICY', policy)
    monkeypatch.setattr(buildlib, '_known_repositories', lambda: frozenset({str(repository.id)}))
    root = tmp_path / 'pi-build'
    (root / 'scripts').mkdir(parents=True)
    (root / 'bootstrap').mkdir()
    (root / 'scripts/build.py').write_text('print(1)\n', encoding='utf-8')
    (root / 'bootstrap/buildlib-run').write_bytes(SHIM)
    (root / 'bootstrap/python.lock').write_bytes(LOCK)
    (root / 'pyproject.toml').write_text(_pyproject(), encoding='utf-8')
    (root / 'uv.lock').write_text(_uv_lock(), encoding='utf-8')
    _write_policy(policy, _policy_text(enrolled=_enrolled_text()))
    return root, repository, policy


def test_enrolled_conforming_consumer_is_clean(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    assert buildlib._check(root, repository) == []


def test_exempt_native_repository_is_clean(project: tuple[Path, Repository, Path]) -> None:
    root, repository, policy = project
    _write_policy(policy, _policy_text(exempt=_exempt_text()))
    assert buildlib._check(root, repository) == []


def test_assess_repository_is_informational(project: tuple[Path, Repository, Path]) -> None:
    root, repository, policy = project
    _write_policy(policy, _policy_text(assess=(str(repository.id),)))
    findings = buildlib._check(root, repository)
    assert [(finding.severity, finding.kind) for finding in findings] == [('info', 'violation')]
    assert 'assessment pending' in findings[0].message


def test_unclassified_active_repository_is_informational(project: tuple[Path, Repository, Path]) -> None:
    root, repository, policy = project
    _write_policy(policy, _policy_text())
    findings = buildlib._check(root, repository)
    assert [(finding.severity, finding.kind) for finding in findings] == [('info', 'violation')]
    assert 'unclassified buildlib disposition' in findings[0].message


def test_missing_dependency_is_a_violation(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    (root / 'pyproject.toml').write_text(_pyproject(()), encoding='utf-8')
    findings = buildlib._check(root, repository)
    matched = [finding for finding in findings if 'missing laputa-buildlib dependency' in finding.message]
    assert len(matched) == 1
    assert matched[0].kind == 'violation'
    assert matched[0].severity == 'error'


def test_range_pin_is_a_violation(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    (root / 'pyproject.toml').write_text(_pyproject(('laputa-buildlib>=0.2.0',)), encoding='utf-8')
    findings = buildlib._check(root, repository)
    matched = [finding for finding in findings if 'pinned exactly' in finding.message]
    assert len(matched) == 1
    assert matched[0].kind == 'violation'


def test_uv_lock_digest_mismatch_is_a_violation(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    (root / 'uv.lock').write_text(_uv_lock(OTHER_SHA), encoding='utf-8')
    findings = buildlib._check(root, repository)
    matched = [finding for finding in findings if 'uv.lock records wheel sha256' in finding.message]
    assert len(matched) == 1
    assert matched[0].kind == 'violation'


def test_sources_lock_digest_mismatch_is_a_violation(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    (root / 'sources.lock.json').write_text(_sources(OTHER_SHA), encoding='utf-8')
    findings = buildlib._check(root, repository)
    matched = [finding for finding in findings if 'sources.lock.json records wheel sha256' in finding.message]
    assert len(matched) == 1
    assert matched[0].kind == 'violation'


def test_missing_bootstrap_shim_is_a_violation(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    (root / 'bootstrap/buildlib-run').unlink()
    findings = buildlib._check(root, repository)
    matched = [finding for finding in findings if 'missing bootstrap shim' in finding.message]
    assert len(matched) == 1
    assert matched[0].kind == 'violation'


def test_modified_bootstrap_shim_is_a_violation(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    (root / 'bootstrap/python.lock').write_bytes(b'modified\n')
    findings = buildlib._check(root, repository)
    matched = [finding for finding in findings if 'not an approved identity' in finding.message]
    assert len(matched) == 1
    assert matched[0].kind == 'violation'


def test_declared_local_bootstrap_difference_is_clean(project: tuple[Path, Repository, Path]) -> None:
    root, repository, policy = project
    local = b'local patched shim\n'
    (root / 'bootstrap/buildlib-run').write_bytes(local)
    _write_policy(policy, _policy_text(enrolled=_enrolled_text(local={'buildlib-run': _sha(local)})))
    assert buildlib._check(root, repository) == []


def test_missing_declared_entrypoint_is_a_violation(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    (root / 'scripts/build.py').unlink()
    findings = buildlib._check(root, repository)
    matched = [finding for finding in findings if 'declared entrypoint' in finding.message]
    assert len(matched) == 1
    assert matched[0].kind == 'violation'


def test_entrypoint_escaping_the_repository_is_a_violation(project: tuple[Path, Repository, Path]) -> None:
    root, repository, policy = project
    _write_policy(policy, _policy_text(enrolled=_enrolled_text(entrypoints=('../outside.py',))))
    findings = buildlib._check(root, repository)
    matched = [finding for finding in findings if 'must be repository-relative' in finding.message]
    assert len(matched) == 1
    assert matched[0].kind == 'violation'


def test_unknown_exempt_repository_is_a_violation(project: tuple[Path, Repository, Path]) -> None:
    root, repository, policy = project
    _write_policy(policy, _policy_text(exempt=_exempt_text() + _exempt_text('ghost/repo')))
    findings = buildlib._check(root, repository)
    matched = [
        finding for finding in findings
        if 'not an active catalog repository' in finding.message and finding.repository == 'ghost/repo'
    ]
    assert len(matched) == 1
    assert matched[0].kind == 'violation'


def test_exempt_without_reason_is_a_violation(project: tuple[Path, Repository, Path]) -> None:
    root, repository, policy = project
    _write_policy(policy, _policy_text(exempt=_exempt_text(reason=None)))
    findings = buildlib._check(root, repository)
    matched = [finding for finding in findings if 'needs a non-empty reason' in finding.message]
    assert len(matched) == 1
    assert matched[0].kind == 'violation'


def test_exempt_without_reassessment_is_a_violation(project: tuple[Path, Repository, Path]) -> None:
    root, repository, policy = project
    _write_policy(policy, _policy_text(exempt=_exempt_text(reassess=None)))
    findings = buildlib._check(root, repository)
    matched = [finding for finding in findings if 'needs a non-empty reassessment condition' in finding.message]
    assert len(matched) == 1
    assert matched[0].kind == 'violation'


def test_expired_exemption_is_a_violation(project: tuple[Path, Repository, Path]) -> None:
    root, repository, policy = project
    _write_policy(policy, _policy_text(exempt=_exempt_text(reassess='2020-01-01')))
    findings = buildlib._check(root, repository)
    matched = [finding for finding in findings if 'expired on 2020-01-01' in finding.message]
    assert len(matched) == 1
    assert matched[0].kind == 'violation'


def test_duplicate_classification_is_a_violation(project: tuple[Path, Repository, Path]) -> None:
    root, repository, policy = project
    _write_policy(policy, _policy_text(enrolled=_enrolled_text(), exempt=_exempt_text()))
    findings = buildlib._check(root, repository)
    matched = [finding for finding in findings if 'classified more than once' in finding.message]
    assert len(matched) == 1
    assert matched[0].kind == 'violation'


def test_rule_is_registered_read_only() -> None:
    rule = next(rule for rule in registered_rules() if rule.id == 'buildlib-usage')
    assert rule.fix is None
    assert rule.commit_message is None
    assert rule.allowed_paths == ()


def test_shipped_policy_is_valid_and_catalogued() -> None:
    policy = buildlib._load_policy()
    known = buildlib._known_repositories()
    groups = (set(policy.enrolled), set(policy.assess), set(policy.exempt))
    classified = set(policy.enrolled) | set(policy.assess) | set(policy.exempt)
    assert classified <= known
    assert sum(len(group) for group in groups) == len(classified)
    assert len(policy.bootstrap_sha256) == 2
