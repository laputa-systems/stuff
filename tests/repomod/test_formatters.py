from __future__ import annotations

from pathlib import Path

import pytest

from repomod.git import run_git
from repomod.rules.formatters import _commands, _formatting_findings
from repomod.types import RepoId, Repository


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("cargo fmt --all --check", ("cargo fmt",)),
        ("cargo +nightly fmt --all", ("cargo fmt",)),
        ("rustfmt --check src/lib.rs", ("rustfmt",)),
        ("uv run --locked ruff format src tests", ("ruff format",)),
        ("prettier --write .", ("prettier",)),
        ("go fmt ./...", ("go fmt",)),
        ("swiftformat --lint .", ("swiftformat",)),
        ("$(ZIG_BIN) fmt --check zzz.zig", ("zig fmt",)),
        ("${ZIG} fmt --check .", ("zig fmt",)),
        ("$(ZIG_BIN) build test", ()),
        ("pip install black", ("black",)),
        ("echo black", ()),
        ("complete -W 'black white' rg", ()),
        (
            "_describe -t $tag 'color name or r,g,b' '(\n"
            "  black blue green red cyan magenta yellow white\n"
            ")'>/dev/null",
            (),
        ),
        (
            "colors=(\n  black\n  white\n)",
            (),
        ),
        (
            "build() {\n  cargo fmt --check\n}",
            ("cargo fmt",),
        ),
    ],
)
def test_formatter_command_detection(source: str, expected: tuple[str, ...]) -> None:
    assert _commands(source) == expected


@pytest.mark.parametrize(
    ("relative", "content"),
    [
        (".swiftlint.yml", "disabled_rules: []\n"),
        ("macos/.swiftlint.yaml", "disabled_rules: []\n"),
        ("Makefile", "lint:\n\tswiftlint lint --strict\n"),
        (".github/workflows/lint.yml", "jobs:\n  lint:\n    steps:\n      - run: nix develop -c swiftlint lint\n"),
        (
            "Package.swift",
            '.package(url: "https://github.com/SimplyDanny/SwiftLintPlugins", from: "1.0.0"),\n'
            '.package(url: "https://github.com/realm/SwiftLint", from: "0.60.0"),\n',
        ),
    ],
)
def test_swiftlint_is_banned_with_bylaws_replacement(
    tmp_path: Path, relative: str, content: str
) -> None:
    run_git(["init", "--quiet"], cwd=tmp_path)
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    run_git(["add", "."], cwd=tmp_path)

    findings = _formatting_findings(tmp_path, Repository(RepoId("acme", "demo"), ("tool",)))

    assert [(finding.file, finding.message) for finding in findings] == [
        (relative, "SwiftLint is banned; use https://github.com/joshuarli/swift-bylaws")
    ]


def test_swift_package_without_swiftlint_is_allowed(tmp_path: Path) -> None:
    run_git(["init", "--quiet"], cwd=tmp_path)
    (tmp_path / "Package.swift").write_text(
        '.package(url: "https://github.com/joshuarli/swift-bylaws", branch: "main"),\n',
        encoding="utf-8",
    )
    run_git(["add", "."], cwd=tmp_path)

    assert _formatting_findings(tmp_path, Repository(RepoId("acme", "demo"), ("tool",))) == []


def test_vendored_formatter_config_is_left_to_its_upstream(tmp_path: Path) -> None:
    run_git(["init", "--quiet"], cwd=tmp_path)
    hook = "repos:\n  - hooks:\n      - id: fmt\n        entry: cargo fmt --all\n"
    for relative in (".pre-commit-config.yaml", "backend/vendor/rtls/.pre-commit-config.yaml"):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(hook, encoding="utf-8")
    run_git(["add", "."], cwd=tmp_path)

    findings = _formatting_findings(tmp_path, Repository(RepoId("acme", "demo"), ("tool",)))

    assert [finding.file for finding in findings] == [".pre-commit-config.yaml"]
