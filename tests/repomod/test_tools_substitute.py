from __future__ import annotations

import json
from pathlib import Path

import pytest

from repomod import paths, substitutes
from repomod.cli import main

_POLICY = r"""version = 1

[producers."acme/gluon"]
label = "Meson, Ninja"
urls = ["github.com/ninja-build"]

[producers."acme/gluon".packages]
apk = ["meson", "ninja", "ninja-build"]
apt = ["ninja-build"]
brew = ["ninja"]

[producers."acme/node-build"]
label = "Node.js"
actions = ["actions/setup-node"]
urls = ["nodejs.org"]

[producers."acme/node-build".packages]
apt = ['nodejs', '^node@\d+(\.\d+)*$']

[producers."acme/llvm"]
label = "Clang and LLVM toolchains"

[producers."acme/llvm".packages]
apt = ['clang', '^clang-\d+$']

[producers."acme/ssh"]
label = "OpenSSH"
urls = ["cdn.openbsd.org/pub/openbsd/openssh"]

[producers."acme/pytest-parallel"]
label = "pytest-xdist"

[producers."acme/pytest-parallel".manifests]
pypi = ["pytest-xdist", "pytest_xdist"]

[producers."acme/rustybench"]
label = "criterion, divan"

[producers."acme/rustybench".manifests]
cargo = ["criterion", "divan"]

[producers."acme/kache"]
label = "sccache, ccache"

[producers."acme/kache".packages]
apt = ["sccache", "ccache"]

[producers."acme/kache".manifests]
cargo = ["sccache"]
"""


@pytest.fixture
def substitute_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    directory = tmp_path / "policy"
    directory.mkdir()
    (directory / "owned-substitutes.toml").write_text(_POLICY, encoding="utf-8")
    monkeypatch.setattr(paths, "POLICY", directory)


def test_package_match_is_case_insensitive_and_one_line_per_producer(
    substitute_policy: None, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["tools", "substitute", "NINJA-BUILD"]) == 0
    assert capsys.readouterr().out == "acme/gluon\tpackage:apk\tninja-build\n"


def test_regex_package_match_reports_the_package_name(
    substitute_policy: None, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["tools", "substitute", "clang-18"]) == 0
    assert capsys.readouterr().out == "acme/llvm\tpackage:apt\tclang-18\n"


def test_action_match_accepts_a_ref(
    substitute_policy: None, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["tools", "substitute", "Actions/Setup-Node@v4"]) == 0
    assert capsys.readouterr().out == "acme/node-build\taction\tactions/setup-node\n"


def test_url_prefix_match(
    substitute_policy: None, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["tools", "substitute", "https://nodejs.org/dist/v22/node.tar.xz"]) == 0
    assert capsys.readouterr().out == "acme/node-build\turl\tnodejs.org\n"


def test_label_match(
    substitute_policy: None, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["tools", "substitute", "openssh"]) == 0
    assert capsys.readouterr().out == "acme/ssh\tlabel\tOpenSSH\n"


def test_no_match_exits_one_with_a_stderr_message(
    substitute_policy: None, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["tools", "substitute", "definitely-not-a-substitute"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "no owned substitute" in captured.err


def test_json_shape(
    substitute_policy: None, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["tools", "substitute", "actions/setup-node@v4", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == [
        {"kind": "action", "matched": "actions/setup-node", "producer": "acme/node-build"}
    ]


def test_manifest_match_reports_the_ecosystem(
    substitute_policy: None, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["tools", "substitute", "pytest-xdist"]) == 0
    assert capsys.readouterr().out == "acme/pytest-parallel\tmanifest:pypi\tpytest-xdist\n"


def test_manifest_match_normalizes_names(
    substitute_policy: None, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["tools", "substitute", "Pytest_Xdist"]) == 0
    assert capsys.readouterr().out == "acme/pytest-parallel\tmanifest:pypi\tpytest-xdist\n"
    assert main(["tools", "substitute", "serde_derive"]) == 1
    assert main(["tools", "substitute", "CRITERION"]) == 0
    assert capsys.readouterr().out == "acme/rustybench\tmanifest:cargo\tcriterion\n"


def test_manifest_lookup_uses_json_shape(
    substitute_policy: None, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["tools", "substitute", "divan", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == [
        {"kind": "manifest:cargo", "matched": "divan", "producer": "acme/rustybench"}
    ]


def test_package_match_wins_over_manifest_for_shared_names(
    substitute_policy: None, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["tools", "substitute", "sccache"]) == 0
    assert capsys.readouterr().out == "acme/kache\tpackage:apt\tsccache\n"


def test_fleet_doc_generated_table_matches_the_policy() -> None:
    text = substitutes.DOCS.read_text(encoding="utf-8")
    assert substitutes.substitution_table(text) == substitutes.render_substitution_table()


def test_update_fleet_doc_repairs_a_hand_edited_row(tmp_path: Path) -> None:
    target = tmp_path / "fleet.md"
    source = substitutes.DOCS.read_text(encoding="utf-8")
    target.write_text(
        source.replace("| Git | `laputa-systems/git-build` |", "| Git | `example/wrong` |", 1),
        encoding="utf-8",
    )

    assert substitutes.update_fleet_doc(target) is True

    assert substitutes.substitution_table(target.read_text(encoding="utf-8")) == (
        substitutes.render_substitution_table()
    )


def test_module_write_docs_uses_the_documented_entry_point(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "fleet.md"
    source = substitutes.DOCS.read_text(encoding="utf-8")
    target.write_text(
        source.replace("| mold | `joshuarli/mold` |", "| mold | `example/wrong` |", 1),
        encoding="utf-8",
    )
    monkeypatch.setattr(substitutes, "DOCS", target)

    assert substitutes.main(["--write-docs"]) == 0

    assert "docs/fleet.md: updated" in capsys.readouterr().out
    assert substitutes.substitution_table(target.read_text(encoding="utf-8")) == (
        substitutes.render_substitution_table()
    )
