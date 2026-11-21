from __future__ import annotations

from pathlib import Path

from repomod.rules.ci_workflow import _ci_workflow_findings, _ci_workflow_fix
from repomod.types import RepoId, Repository

PULL_REQUEST = "on:\n  pull_request:\njobs:\n  ci:\n    runs-on: ubuntu-26.04-arm\n    steps:\n"


def repository(*tags: str) -> Repository:
    return Repository(RepoId("acme", "demo"), tags or ("tool",))


def workflow(root: Path, name: str, source: str) -> None:
    path = root / ".github" / "workflows" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


def makefile(root: Path, source: str = "test:\n\tcargo test\n") -> None:
    (root / "Makefile").write_text(source, encoding="utf-8")


def found(root: Path, project: Repository) -> list[tuple[str | None, bool]]:
    return [(item.file, item.fixable) for item in _ci_workflow_findings(root, project)]


def test_only_a_pull_request_make_test_or_test_ci_step_satisfies_the_rule(tmp_path: Path) -> None:
    makefile(tmp_path)
    for step in (
        "make test",
        "make test-ci TARGET=x",
        'make test-ci TARGET="${{ matrix.target }}" PLATFORM="${{ matrix.platform }}"',
    ):
        workflow(tmp_path, "ci.yml", PULL_REQUEST + f"      - run: {step}\n")
        assert found(tmp_path, repository()) == [], step

    for step in (
        "make test-mypypi-native",
        "make testing",
        "echo make test-ci-extra",
        'make test-ci TARGET="a b"',
        'make test-ci TARGET="${{ matrix.target }} x"',
    ):
        workflow(tmp_path, "ci.yml", PULL_REQUEST + f"      - run: {step}\n")
        assert found(tmp_path, repository()) == [(".github/workflows/ci.yml", False)], step

    workflow(tmp_path, "ci.yml", "on:\n  push:\njobs:\n  ci:\n    steps:\n      - run: make test\n")
    assert found(tmp_path, repository()) == [(".github/workflows/ci.yml", False)]


def test_direct_test_commands_are_reported_per_workflow_and_not_fixable(tmp_path: Path) -> None:
    makefile(tmp_path)
    workflow(tmp_path, "ci.yml", PULL_REQUEST + "      - run: cargo test --locked\n")
    workflow(tmp_path, "web.yml", PULL_REQUEST + "      - run: |\n          pnpm install\n          pnpm run test\n")
    workflow(tmp_path, "docs.yml", PULL_REQUEST + "      - run: mdtool check\n")

    findings = _ci_workflow_findings(tmp_path, repository())

    assert [(item.file, item.fixable) for item in findings] == [
        (".github/workflows/ci.yml", False),
        (".github/workflows/web.yml", False),
    ]
    assert "make test" in findings[0].message
    assert _ci_workflow_fix(tmp_path, repository()) == {}


def test_missing_ci_workflow_is_fixed_with_a_make_test_workflow(tmp_path: Path) -> None:
    makefile(tmp_path)
    workflow(tmp_path, "lint.yml", "on:\n  pull_request:\njobs:\n  lint:\n    steps:\n      - run: make lint\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\n', encoding="utf-8")
    (tmp_path / "demo.py").write_text("print(1)\n", encoding="utf-8")

    assert found(tmp_path, repository()) == [(".github/workflows/ci.yml", True)]
    plan = _ci_workflow_fix(tmp_path, repository())
    assert set(plan) == {".github/workflows/ci.yml"}
    rendered = plan[".github/workflows/ci.yml"]
    assert "  pull_request:\n" in rendered
    assert "run: make test\n" in rendered
    assert "uv python install 3.15" in rendered
    workflow(tmp_path, "ci.yml", rendered)

    assert found(tmp_path, repository()) == []
    assert _ci_workflow_fix(tmp_path, repository()) == {}


def test_a_repository_without_a_test_target_needs_one_first(tmp_path: Path) -> None:
    makefile(tmp_path, "lint:\n\tcargo clippy\n")
    assert found(tmp_path, repository()) == [("Makefile", False)]
    (tmp_path / "Makefile").unlink()
    assert found(tmp_path, repository()) == [("Makefile", False)]
    assert _ci_workflow_fix(tmp_path, repository()) == {}


def test_an_existing_ci_workflow_without_tests_is_a_manual_repair(tmp_path: Path) -> None:
    makefile(tmp_path)
    workflow(tmp_path, "ci.yml", PULL_REQUEST + "      - run: docker run --rm tests\n")

    assert found(tmp_path, repository()) == [(".github/workflows/ci.yml", False)]
    assert _ci_workflow_fix(tmp_path, repository()) == {}


def test_pristine_forks_are_skipped_and_diverged_forks_read_every_workflow(tmp_path: Path) -> None:
    makefile(tmp_path)
    workflow(tmp_path, "ci.yml", PULL_REQUEST + "      - run: cargo test\n")

    assert found(tmp_path, repository("tool", "fork")) == []
    assert found(tmp_path, repository("tool", "fork", "fork-diverged")) == [(".github/workflows/ci.yml", False)]


def test_unsupported_workflow_shapes_name_the_construct(tmp_path: Path) -> None:
    makefile(tmp_path)
    run = '      - run: make test\n'
    def trigger(options: str) -> str:
        return PULL_REQUEST.replace('  pull_request:\n', f'  pull_request:\n    {options}\n') + run
    def job(option: str) -> str:
        return PULL_REQUEST.replace('    runs-on:', f'    {option}\n    runs-on:') + run
    cases = [
        (PULL_REQUEST + '      - run: make test\n        if: false\n', 'step-level if'),
        (job('if: ${{ false }}'), 'job-level if'),
        (PULL_REQUEST + '      - run: make test\n        continue-on-error: true\n', 'step continue-on-error'),
        (job('continue-on-error: true'), 'job continue-on-error'),
        (PULL_REQUEST + '      - run: make test || true\n', 'shell operator ||'),
        (PULL_REQUEST + '      - run: make -n test\n', 'make flag -n'),
        (trigger('paths: [src/**]'), 'pull_request paths'),
        (trigger('paths-ignore: [docs/**]'), 'pull_request paths-ignore'),
        (trigger('branches-ignore: [main]'), 'pull_request branches-ignore'),
        (trigger('types: [opened, reopened]'), 'pull_request types'),
        ('on: pull_request\njobs:\n  ci:\n    uses: acme/demo/.github/workflows/test.yml@main\n',
         'reusable-workflow job uses'),
        (PULL_REQUEST + '      - run: make test\n        shell: pwsh\n', 'step shell'),
        (PULL_REQUEST.replace('    steps:', '    defaults:\n      run:\n        shell: pwsh\n    steps:') + run,
         'step shell'),
        ('defaults:\n  run:\n    shell: pwsh\n' + PULL_REQUEST + run, 'step shell'),
        (PULL_REQUEST + '      - run: |\n          make test\n          echo done\n', 'multi-line'),
    ]
    for source, expected in cases:
        workflow(tmp_path, 'ci.yml', source)
        findings = _ci_workflow_findings(tmp_path, repository())
        assert len(findings) == 1, source
        assert expected in findings[0].message, (source, findings)


def test_supported_workflow_shapes(tmp_path: Path) -> None:
    makefile(tmp_path)
    for source in (
        PULL_REQUEST + '      - run: make test\n',
        PULL_REQUEST + '      - run: make test-ci\n',
        PULL_REQUEST + '      - run: make test-ci TARGET=x\n',
        PULL_REQUEST.replace('    runs-on:', '    strategy:\n      matrix:\n        target: [one, two]\n    runs-on:')
        + '      - run: make test\n',
        PULL_REQUEST.replace('    steps:', '    defaults:\n      run:\n        working-directory: sub\n    steps:')
        + '      - run: make test\n',
        PULL_REQUEST.replace(
            '    steps:', '    defaults:\n      run:\n        shell: bash -euo pipefail {0}\n    steps:'
        )
        + '      - run: make test\n',
    ):
        workflow(tmp_path, 'ci.yml', source)
        assert _ci_workflow_findings(tmp_path, repository()) == [], source


def test_invalid_yaml_is_operational_even_with_a_valid_workflow(tmp_path: Path) -> None:
    makefile(tmp_path)
    workflow(tmp_path, 'a.yml', PULL_REQUEST + '      - run: make test\n')
    workflow(tmp_path, 'z.yml', 'on: [\n')
    findings = _ci_workflow_findings(tmp_path, repository())
    assert len(findings) == 1
    assert findings[0].kind == 'operational'
    assert 'cannot parse workflow YAML' in findings[0].message


def test_ambiguous_branches_are_reported(tmp_path: Path, monkeypatch) -> None:
    from repomod.rules import ci_workflow

    monkeypatch.setattr(ci_workflow, "_local_default_branch", lambda root: None)
    makefile(tmp_path)
    workflow(tmp_path, 'ci.yml', PULL_REQUEST.replace(
        '  pull_request:\n', '  pull_request:\n    branches: [main]\n'
    ) + '      - run: make test\n')
    findings = _ci_workflow_findings(tmp_path, repository())
    assert 'ambiguous pull_request branches' in findings[0].message


def test_fleet_workflow_shapes(tmp_path: Path) -> None:
    makefile(tmp_path)
    srv = PULL_REQUEST + '      - run: make test\n'
    workflow(tmp_path, 'ci.yml', srv)
    assert _ci_workflow_findings(tmp_path, repository()) == []
    loc = PULL_REQUEST + (
        "      - run: |\n"
        "          docker run image sh -ec '\n"
        "            cargo clippy\n"
        "            make test\n"
        "          '\n"
    )
    workflow(tmp_path, 'ci.yml', loc)
    findings = _ci_workflow_findings(tmp_path, repository())
    assert len(findings) == 1
    assert 'cannot verify failure propagation' in findings[0].message
    assert 'single-line make test-ci' in findings[0].message
