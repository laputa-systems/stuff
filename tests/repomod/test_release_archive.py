from pathlib import Path

import pytest

from repomod.rules.release_archive import _findings
from repomod.types import Finding, RepoId, Repository


def check(root: Path, text: str, name: str = "demo", owner: str = "laputa-systems") -> list[Finding]:
    workflow = root / ".github/workflows/release.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text("jobs:\n  release:\n    steps:\n      - run: |\n          gh release create v1\n" + text + "\n")
    return _findings(root, Repository(RepoId(owner, name), ("tool",)))


@pytest.mark.parametrize("construct", [
    'zip -9 --junk-paths dist/demo.zip demo',
    'ditto -c -k demo dist/demo.zip',
    "zipfile.ZipFile('dist/demo.zip', 'w')",
    'tar czf dist/demo.tar.gz demo',
    'gh release upload v1 dist/demo.tar.zst',
    'gh release upload v1 dist/demo.tar',
    'tools/make-archive dist/demo.zip demo',
])
def test_nonstandard_constructs_report_line_and_construct(tmp_path: Path, construct: str) -> None:
    findings = check(tmp_path, "          " + construct)
    assert [(f.file, f.line, f.message) for f in findings] == [
        (".github/workflows/release.yml", 6, f"release archive must be tar.xz: {construct}")
    ]


@pytest.mark.parametrize("install", [
    "apk add --no-cache bash file tar zstd libxkbcommon-dev libffi-dev",
    "apt-get install -y curl tar libxkbcommon-dev libffi-dev",
])
def test_installing_tar_is_not_an_archive_construct(tmp_path: Path, install: str) -> None:
    assert check(tmp_path, "          " + install) == []


def test_softprops_zip_asset(tmp_path: Path) -> None:
    findings = check(
        tmp_path, "      - uses: softprops/action-gh-release@v2\n        with:\n          files: dist/*.zip"
    )
    assert [(f.file, f.line, f.message) for f in findings] == [
        (".github/workflows/release.yml", 8, "release archive must be tar.xz: files: dist/*.zip")
    ]


def test_cargo_dist_explicit_zip(tmp_path: Path) -> None:
    (tmp_path / "dist-workspace.toml").write_text('[dist]\nunix-archive = ".zip"\nwindows-archive = ".zip"\n')
    findings = check(tmp_path, "          cargo-dist plan")
    assert [(f.file, f.line, f.message) for f in findings] == [
        ("dist-workspace.toml", 2, "cargo-dist unix-archive is .zip")
    ]
    (tmp_path / "dist-workspace.toml").write_text('[dist]\nwindows-archive = ".zip"\n')
    assert check(tmp_path, "          cargo-dist plan") == []


@pytest.mark.parametrize(("owner", "name", "asset"), [
    ("laputa-systems", "python-build", "cpython-3-install_only_stripped.tar.gz"),
    ("joshuarli", "pi-build", "agent-intercom-1.tgz"),
    ("joshuarli", "pytest-parallel", "package.whl"),
])
def test_exempt_assets(tmp_path: Path, owner: str, name: str, asset: str) -> None:
    assert check(tmp_path, f"          gh release upload v1 {asset}", name, owner) == []


def test_tgz_outside_the_npm_pack_exemption_is_reported(tmp_path: Path) -> None:
    findings = check(tmp_path, "          gh release upload v1 package-1.tgz", "other", "acme")
    assert [f.message for f in findings] == ["release archive must be tar.xz: gh release upload v1 package-1.tgz"]


def test_valid_tar_xz(tmp_path: Path) -> None:
    assert check(
        tmp_path,
        "          tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner "
        "-cJf dist/archives/demo.tar.xz -C dist/demo demo\n"
        "          gh release create v1 dist/archives/*.tar.xz",
    ) == []


def test_invoked_packaging_script(tmp_path: Path) -> None:
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/package.sh").write_text('#!/bin/sh\nzip -9 out.zip bin\n')
    findings = check(tmp_path, "          ./scripts/package.sh")
    assert [(f.file, f.line, f.message) for f in findings] == [
        ("scripts/package.sh", 2, "release archive must be tar.xz: zip -9 out.zip bin")
    ]


def test_called_workflow_archive(tmp_path: Path) -> None:
    workflows = tmp_path / ".github/workflows"
    workflows.mkdir(parents=True)
    (workflows / "build.yml").write_text(
        "jobs:\n  build:\n    steps:\n      - uses: actions/upload-artifact@v4\n"
        "        with:\n          path: release.tar.gz\n"
    )
    findings = check(tmp_path, "      - uses: ./.github/workflows/build.yml")
    assert [(f.file, f.line, f.message) for f in findings] == [
        (".github/workflows/build.yml", 6, "release archive must be tar.xz: path: release.tar.gz")
    ]


def test_multiline_tar_creation(tmp_path: Path) -> None:
    findings = check(tmp_path, "          tar --sort=name \\\n            -C stage -czf out.tar.gz file")
    assert [(f.file, f.line, f.message) for f in findings] == [
        (".github/workflows/release.yml", 6,
         "release archive must be tar.xz: tar --sort=name  -C stage -czf out.tar.gz file")
    ]
