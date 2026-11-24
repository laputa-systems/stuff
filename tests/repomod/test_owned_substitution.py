from __future__ import annotations

from pathlib import Path

import pytest

from repomod.rules import owned_substitution
from repomod.rules import rules as registered_rules
from repomod.types import RepoId, Repository

REPO = "acme/consumer"
OTHER = "acme/other"
POLICY_OWNER = "acme"


def _owned_tools(producers: tuple[str, ...]) -> str:
    lines = [
        "version = 1",
        'maintainer = "Acme"',
        'procedure = "https://example.invalid/procedure"',
        'owners = ["acme"]',
        'install_manifest = ".local/state/install.json"',
        "",
        "[producers]",
    ]
    for producer in producers:
        lines.extend([
            f'[producers."{producer}"]',
            "",
            f'[producers."{producer}".commands]',
            'tool = { gap = "no footer yet" }',
            "",
        ])
    lines.extend(["[not_applicable]", ""])
    return "\n".join(lines)


def _substitutes_text(
    *,
    extra_producers: str = "",
    exempt: str = "",
) -> str:
    return f"""version = 1

[producers."acme/gluon"]
urls = ["github.com/ninja-build"]

[producers."acme/gluon".packages]
apk = ["meson", "ninja", "ninja-build", "samurai"]
apt = ["meson", "ninja-build"]
brew = ["meson", "ninja"]
dnf = ["meson", "ninja-build"]
pacman = ["meson", "ninja", "samurai"]

[producers."acme/cmake-build"]
urls = ["cmake.org"]

[producers."acme/cmake-build".packages]
apk = ["cmake"]
apt = ["cmake"]
brew = ["cmake"]
dnf = ["cmake"]
pacman = ["cmake"]

[producers."acme/llvm-prebuilt-musl"]
urls = ["apt.llvm.org"]

[producers."acme/llvm-prebuilt-musl".packages]
apk = ["clang", "lld", "llvm", "^clang-?\\\\d+$"]
apt = ["clang", "lld", "llvm", "^clang-\\\\d+$", "^lld-\\\\d+$", "^llvm-\\\\d+$"]
brew = ["llvm"]
dnf = ["clang", "lld", "llvm"]
pacman = ["clang", "lld", "llvm"]

[producers."acme/node-build"]
actions = ["actions/setup-node"]
urls = ["nodejs.org"]

[producers."acme/node-build".packages]
apk = ["nodejs", "npm"]
apt = ["nodejs", "npm"]
brew = ["node", "^node@\\\\d+(\\\\.\\\\d+)*$"]
dnf = ["nodejs", "npm"]
pacman = ["nodejs", "npm"]

[producers."acme/python-build"]
actions = ["actions/setup-python", "astral-sh/setup-uv"]
urls = ["python.org/ftp"]

[producers."acme/python-build".packages]
apk = ["^python3([.-].*)?$"]
apt = ["^python3([.-].*)?$"]
brew = ["python3"]
dnf = ["^python3([.-].*)?$"]
pacman = ["python", "^python3([.-].*)?$"]

[producers."acme/git-build".packages]
apk = ["git"]
apt = ["git"]
brew = ["git"]
dnf = ["git"]
pacman = ["git"]

[producers."acme/git-build"]
urls = ["github.com/git/git"]

[producers."acme/mold"]
urls = ["github.com/rui314/mold"]

[producers."acme/mold".packages]
apk = ["mold"]
apt = ["mold"]
brew = ["mold"]
dnf = ["mold"]
pacman = ["mold"]
{extra_producers}{exempt}"""


PRODUCERS = (
    "acme/gluon",
    "acme/cmake-build",
    "acme/llvm-prebuilt-musl",
    "acme/node-build",
    "acme/python-build",
    "acme/git-build",
    "acme/mold",
)


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Repository, Path]:
    repository = Repository(RepoId.parse(REPO), ("build",))
    policy = tmp_path / "policy"
    policy.mkdir()
    (policy / "owned-tools.toml").write_text(_owned_tools(PRODUCERS), encoding="utf-8")
    (policy / "owned-substitutes.toml").write_text(_substitutes_text(), encoding="utf-8")
    monkeypatch.setattr(owned_substitution.paths, "POLICY", policy)
    monkeypatch.setattr(
        owned_substitution, "_known_repositories", lambda: frozenset({REPO, OTHER})
    )
    root = tmp_path / "consumer"
    root.mkdir()
    return root, repository, policy


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_clean_repository_has_no_findings(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(root, "scripts/build.sh", "#!/bin/sh\ngit clone https://example.invalid/repo\nmake\n")
    assert owned_substitution._check(root, repository) == []


def test_apk_add_with_continuation_and_pins(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(
        root,
        "Dockerfile",
        "FROM alpine\nRUN apk add --no-cache \\\n    build-base meson=1.11.1-r0 ninja-build=1.13.2-r1 samurai curl\n",
    )
    findings = owned_substitution._check(root, repository)
    labels = [finding.message.split(" duplicates")[0] for finding in findings]
    assert any("package 'meson'" in label for label in labels)
    assert any("package 'ninja-build'" in label for label in labels)
    assert any("package 'samurai'" in label for label in labels)
    assert all(finding.line == 2 for finding in findings)
    assert all("acme/gluon" in finding.message for finding in findings)
    assert all("buildlib.tools" in finding.message for finding in findings)


def test_apt_get_install_flags_versioned_packages(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(
        root,
        "scripts/setup.sh",
        "#!/bin/sh\n"
        "sudo apt-get update && sudo apt-get install -y --no-install-recommends \\\n"
        "    meson ninja-build cmake clang-19 lld-19 python3.12 git mold curl\n",
    )
    findings = owned_substitution._check(root, repository)
    producers = {finding.message.split("owned producer ")[1].split(";")[0] for finding in findings}
    assert producers == {
        "acme/gluon", "acme/cmake-build", "acme/llvm-prebuilt-musl",
        "acme/python-build", "acme/git-build", "acme/mold",
    }
    assert any("package 'clang-19'" in finding.message for finding in findings)
    assert any("package 'python3.12'" in finding.message for finding in findings)


def test_brew_install_and_dnf_install(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(root, "Makefile", "setup:\n\tbrew install meson ninja pkgconf\n\tdnf install -y cmake nodejs\n")
    findings = owned_substitution._check(root, repository)
    labels = [finding.message.split(" duplicates")[0] for finding in findings]
    assert any("package 'meson' installed by brew" in label for label in labels)
    assert any("package 'ninja' installed by brew" in label for label in labels)
    assert any("package 'cmake' installed by dnf" in label for label in labels)
    assert any("package 'nodejs' installed by dnf" in label for label in labels)


def test_pacman_sync_flags_packages(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(root, "docker/arch.Dockerfile", "RUN pacman -S --needed --noconfirm mold git curl\n")
    findings = owned_substitution._check(root, repository)
    labels = [finding.message.split(" duplicates")[0] for finding in findings]
    assert any("package 'mold' installed by pacman" in label for label in labels)
    assert any("package 'git' installed by pacman" in label for label in labels)


def test_pacman_query_is_not_an_install(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(root, "scripts/check.sh", "#!/bin/sh\npacman -Q git mold\n")
    assert owned_substitution._check(root, repository) == []


def test_workflow_setup_actions(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(
        root,
        ".github/workflows/ci.yml",
        "jobs:\n  build:\n    steps:\n"
        "      - uses: actions/setup-node@v4\n"
        "      - uses: actions/setup-python@v5\n"
        "        with:\n"
        "          python-version: '3.12'\n"
        "      - uses: astral-sh/setup-uv@v10\n"
        "        with:\n"
        "          version: 0.13.7\n"
        "      - run: uv python install 3.15\n",
    )
    findings = owned_substitution._check(root, repository)
    producers = {
        finding.message.split("owned producer ")[1].split(";")[0]
        for finding in findings
    }
    assert producers == {"acme/node-build", "acme/python-build"}
    assert sum("action 'actions/setup-node'" in f.message for f in findings) == 1
    assert sum("action 'actions/setup-python'" in f.message for f in findings) == 1
    assert sum("action 'astral-sh/setup-uv'" in f.message for f in findings) == 1
    assert sum("command 'uv python install'" in f.message for f in findings) == 1


def test_setup_uv_without_python_is_clean(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(
        root,
        ".github/workflows/lint.yml",
        "jobs:\n  lint:\n    steps:\n"
        "      - uses: astral-sh/setup-uv@v10\n"
        "        with:\n"
        "          version: 0.13.7\n"
        "      - run: uv sync\n"
        "      - run: make lint\n",
    )
    assert owned_substitution._check(root, repository) == []


def test_setup_uv_with_python_version_input(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(
        root,
        ".github/workflows/ci.yml",
        "jobs:\n  test:\n    steps:\n"
        "      - uses: astral-sh/setup-uv@v10\n"
        "        with:\n"
        "          python-version: '3.13'\n"
        "      - run: uv run pytest\n",
    )
    findings = owned_substitution._check(root, repository)
    assert any("action 'astral-sh/setup-uv'" in finding.message for finding in findings)


def test_download_urls(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(
        root,
        "scripts/fetch.sh",
        "#!/bin/sh\n"
        "curl -fsSL https://nodejs.org/dist/v22.0.0/node-v22.0.0-linux-x64.tar.xz -o node.tar.xz\n"
        "curl -fsSL https://github.com/ninja-build/ninja/releases/download/v1.12.1/ninja-linux.zip -o ninja.zip\n"
        "curl -fsSL https://cmake.org/files/v3.30.0/cmake-3.30.0.tar.gz -o cmake.tgz\n"
        "curl -fsSL https://github.com/ninja-build-evil.example/x.tgz -o ok.tgz\n"
        "curl -fsSL https://example.invalid/dist/node.tar.xz -o other.tgz\n",
    )
    findings = owned_substitution._check(root, repository)
    labels = [finding.message.split(" duplicates")[0] for finding in findings]
    assert sum("nodejs.org" in label for label in labels) == 1
    assert sum("ninja-build/ninja" in label for label in labels) == 1
    assert sum("cmake.org" in label for label in labels) == 1
    producers = {f.message.split("owned producer ")[1].split(";")[0] for f in findings}
    assert producers == {"acme/node-build", "acme/gluon", "acme/cmake-build"}


def test_git_package_install_flagged_but_git_command_is_not(
    project: tuple[Path, Repository, Path],
) -> None:
    root, repository, _ = project
    _write(
        root,
        "scripts/deploy.sh",
        "#!/bin/sh\n"
        "git clone https://example.invalid/repo.git\n"
        "git -C repo status\n"
        "apk add --no-cache git curl\n"
        "apt-get source git\n",
    )
    findings = owned_substitution._check(root, repository)
    assert len(findings) == 1
    assert "package 'git' installed by apk" in findings[0].message
    assert "acme/git-build" in findings[0].message


def test_clang_format_and_comments_are_not_flagged(
    project: tuple[Path, Repository, Path],
) -> None:
    root, repository, _ = project
    _write(
        root,
        "scripts/build.sh",
        "#!/bin/sh\n"
        "# apk add meson ninja would go here\n"
        "clang-format --version\n"
        "echo meson ninja cmake\n"
        "apt-get install -y clang-format curl\n",
    )
    assert owned_substitution._check(root, repository) == []


def test_ignored_directories_are_not_scanned(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(root, "vendor/pkg/Dockerfile", "RUN apk add meson\n")
    _write(root, "node_modules/pkg/scripts/install.sh", "apk add meson\n")
    _write(root, "tests/fixtures/Dockerfile", "RUN apk add meson\n")
    assert owned_substitution._check(root, repository) == []


def test_surface_kinds(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(root, "docker/dev.Dockerfile", "RUN apk add meson\n")
    _write(root, "docker/nested/env.sh", "apk add ninja\n")
    _write(root, "sub/mk/extra.mk", "install:\n\tapt-get install -y meson\n")
    _write(root, "flake.nix", "{ pkgs }: pkgs.mkShell { buildInputs = [ ]; } # apk add meson\n")
    findings = owned_substitution._check(root, repository)
    files = {finding.file for finding in findings}
    assert files == {"docker/dev.Dockerfile", "docker/nested/env.sh", "sub/mk/extra.mk"}


def test_exemption_suppresses_matching_producer(project: tuple[Path, Repository, Path]) -> None:
    root, repository, policy = project
    _write(root, "Dockerfile", "RUN apk add meson mold\n")
    (policy / "owned-substitutes.toml").write_text(
        _substitutes_text(
            exempt=(
                '\n[exempt."acme/consumer".producers."acme/gluon"]\n'
                'reason = "The producer publishes no release for this platform."\n'
                'reassess = "Reassess when acme/gluon ships the platform."\n'
            )
        ),
        encoding="utf-8",
    )
    findings = owned_substitution._check(root, repository)
    assert len(findings) == 1
    assert "package 'mold'" in findings[0].message
    assert "acme/mold" in findings[0].message


def test_stale_exemption_is_a_finding(project: tuple[Path, Repository, Path]) -> None:
    root, repository, policy = project
    _write(root, "Dockerfile", "RUN apk add mold\n")
    (policy / "owned-substitutes.toml").write_text(
        _substitutes_text(
            exempt=(
                '\n[exempt."acme/consumer".producers."acme/gluon"]\n'
                'reason = "Deferred until the named producer gap is fixed."\n'
                'reassess = "Reassess when the gap closes."\n'
            )
        ),
        encoding="utf-8",
    )
    findings = owned_substitution._check(root, repository)
    stale = [finding for finding in findings if "stale exemption" in finding.message]
    assert len(stale) == 1
    assert "acme/gluon" in stale[0].message


def test_exemption_for_unknown_producer_is_a_policy_finding(
    project: tuple[Path, Repository, Path],
) -> None:
    root, repository, policy = project
    _write(root, "Dockerfile", "RUN apk add mold\n")
    (policy / "owned-substitutes.toml").write_text(
        _substitutes_text(
            exempt=(
                '\n[exempt."acme/consumer".producers."acme/not-a-producer"]\n'
                'reason = "Some reason."\n'
                'reassess = "Later."\n'
            )
        ),
        encoding="utf-8",
    )
    findings = owned_substitution._check(root, repository)
    assert any("unknown producer" in finding.message for finding in findings)


def test_exemption_for_non_catalog_repository_is_reported_once(
    project: tuple[Path, Repository, Path],
) -> None:
    _, _, policy = project
    (policy / "owned-substitutes.toml").write_text(
        _substitutes_text(
            exempt=(
                '\n[exempt."ghost/repo".producers."acme/gluon"]\n'
                'reason = "Some reason."\n'
                'reassess = "Later."\n'
            )
        ),
        encoding="utf-8",
    )
    first = Repository(RepoId.parse("acme/aardvark"), ())
    findings = owned_substitution._semantic_policy_findings(
        first,
        owned_substitution._load_policy(),
        frozenset({"acme/aardvark", "acme/consumer"}),
        frozenset({name.casefold() for name in PRODUCERS}),
    )
    assert any("not an active catalog repository" in finding.message for finding in findings)


def test_exemption_without_reason_is_a_policy_error(
    project: tuple[Path, Repository, Path],
) -> None:
    root, repository, policy = project
    (policy / "owned-substitutes.toml").write_text(
        _substitutes_text(
            exempt='\n[exempt."acme/consumer".producers."acme/gluon"]\nreassess = "Later."\n'
        ),
        encoding="utf-8",
    )
    findings = owned_substitution._check(root, repository)
    assert any(
        finding.kind == "operational" and "non-empty reason" in finding.message
        for finding in findings
    )


def test_unknown_manager_is_a_policy_error(project: tuple[Path, Repository, Path]) -> None:
    root, repository, policy = project
    text = _substitutes_text().replace(
        '[producers."acme/gluon".packages]\napk',
        '[producers."acme/gluon".packages]\nzypper',
        1,
    )
    (policy / "owned-substitutes.toml").write_text(text, encoding="utf-8")
    findings = owned_substitution._check(root, repository)
    assert any("unknown manager" in finding.message for finding in findings)


def test_missing_policy_is_operational(project: tuple[Path, Repository, Path]) -> None:
    root, repository, policy = project
    (policy / "owned-substitutes.toml").unlink()
    findings = owned_substitution._check(root, repository)
    assert len(findings) == 1
    assert findings[0].kind == "operational"


def test_variable_package_list_is_expanded(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(
        root,
        "scripts/setup.sh",
        "#!/bin/sh\n"
        "packages='curl meson ninja-build'\n"
        "apt-get install -y $packages\n",
    )
    findings = owned_substitution._check(root, repository)
    labels = [finding.message.split(" duplicates")[0] for finding in findings]
    assert any("package 'meson'" in label for label in labels)
    assert any("package 'ninja-build'" in label for label in labels)


def test_shipped_policy_is_valid_and_uses_owned_producers() -> None:
    policy = owned_substitution._load_policy()
    owned = owned_substitution._owned_producers()
    assert policy.producers
    assert all(name.casefold() in owned for name in policy.producers)
    assert not policy.exempt


def test_rule_is_registered_read_only() -> None:
    rule = next(rule for rule in registered_rules() if rule.id == "owned-tool-substitution")
    assert rule.fix is None
    assert rule.commit_message is None
    assert rule.allowed_paths == ()


def test_producer_may_install_the_upstream_it_reproduces(project: tuple[Path, Repository, Path]) -> None:
    root, _, _ = project
    producer = Repository(RepoId.parse("acme/gluon"), ("build",))
    _write(root, "Dockerfile", "FROM alpine\nRUN apk add --no-cache meson ninja cmake\n")
    findings = owned_substitution._check(root, producer)
    assert [finding.message.split(" duplicates")[0] for finding in findings] == ["package 'cmake' installed by apk"]
