from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest

from repomod import owned_tools_image, paths
from repomod.rules import tools_lock

LOCK_PATH = owned_tools_image.LOCK_PATH
BOOTSTRAP_DIR = owned_tools_image.BOOTSTRAP_DIR
IMAGE_POLICY_PATH = owned_tools_image.IMAGE_POLICY_PATH
DOCKERFILE_PATH = owned_tools_image.DOCKERFILE_PATH
MUSL_TOOLCHAIN_PATH = paths.POLICY / "musl-toolchain.toml"


def _dockerfile() -> str:
    return owned_tools_image.dockerfile_text()


def test_shipped_lock_matches_policy() -> None:
    assert LOCK_PATH.read_text(encoding="utf-8") == owned_tools_image.render_lock()


def test_shipped_lock_is_schema_one_with_image_tools() -> None:
    document = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    assert document["schema"] == 1
    assert sorted(document["tools"]) == owned_tools_image.image_tools()
    approved = tools_lock._load_policy()
    for tool in document["tools"]:
        assert document["tools"][tool] == approved[tool]


def test_shipped_bootstrap_copies_match_vendored_shims() -> None:
    sources = owned_tools_image.bootstrap_sources()
    shipped = {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(BOOTSTRAP_DIR.iterdir())
        if path.is_file()
    }
    assert shipped == sources


def test_bootstrap_dir_has_no_stray_files() -> None:
    assert {path.name for path in BOOTSTRAP_DIR.iterdir()} == set(
        owned_tools_image.bootstrap_sources()
    )


def test_drift_reports_lock_and_bootstrap_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(owned_tools_image, "LOCK_PATH", tmp_path / "tools.lock.json")
    monkeypatch.setattr(owned_tools_image, "BOOTSTRAP_DIR", tmp_path / "bootstrap")
    (tmp_path / "tools.lock.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "bootstrap").mkdir()
    problems = owned_tools_image.drift()
    assert any("tools.lock.json" in problem for problem in problems)
    assert any("buildlib-run" in problem for problem in problems)
    assert any("python.lock" in problem for problem in problems)


def test_image_policy_records_repository_tools_and_digest() -> None:
    policy = owned_tools_image.image_policy()
    assert policy["version"] == 1
    assert policy["reference"] == "oci.17166969.xyz/owned-tools"
    digest = policy["digest"]
    assert digest == "" or re.fullmatch(r"sha256:[0-9a-f]{64}", str(digest))
    assert policy["tools"] == owned_tools_image.image_tools()


def test_dockerfile_base_matches_musl_policy() -> None:
    toolchain = tomllib.loads(MUSL_TOOLCHAIN_PATH.read_text(encoding="utf-8"))
    stable = toolchain["channels"]["stable"]
    dockerfile = _dockerfile()
    assert f"FROM {stable['image']}@{stable['index_digest']} AS fetch" in dockerfile
    assert "FROM scratch" in dockerfile
    assert "COPY --from=fetch /opt/laputa /opt/laputa" in dockerfile


def test_dockerfile_installs_policy_tools() -> None:
    tools = " ".join(owned_tools_image.image_tools())
    assert f"for tool in {tools}; do \\" in _dockerfile()


def test_dockerfile_apk_pins_match_musl_policy() -> None:
    toolchain = tomllib.loads(MUSL_TOOLCHAIN_PATH.read_text(encoding="utf-8"))
    packages = toolchain["channels"]["stable"]["packages"]
    dockerfile = _dockerfile()
    pinned = dict(re.findall(r"^\s+([a-z0-9-]+)=([0-9][^\s\\]*)\s*\\?$", dockerfile, re.MULTILINE))
    assert set(pinned) == {"curl", "ca-certificates", "tar", "xz", "libgcc"}
    for package, version in pinned.items():
        for arch in ("aarch64", "x86_64"):
            assert packages[arch][package] == version, (package, arch)
