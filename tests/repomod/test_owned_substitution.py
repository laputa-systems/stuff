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
label = "Meson, Ninja"
urls = ["github.com/ninja-build"]

[producers."acme/gluon".packages]
apk = ["meson", "ninja", "ninja-build", "samurai"]
apt = ["meson", "ninja-build"]
brew = ["meson", "ninja"]
dnf = ["meson", "ninja-build"]
pacman = ["meson", "ninja", "samurai"]

[producers."acme/cmake-build"]
label = "CMake"
urls = ["cmake.org"]

[producers."acme/cmake-build".packages]
apk = ["cmake"]
apt = ["cmake"]
brew = ["cmake"]
dnf = ["cmake"]
pacman = ["cmake"]

[producers."acme/llvm-prebuilt-musl"]
label = "Clang and LLVM toolchains"
urls = ["apt.llvm.org"]

[producers."acme/llvm-prebuilt-musl".packages]
apk = ["clang", "gcc", "lld", "llvm", "^clang-?\\\\d+$"]
apt = ["clang", "lld", "llvm", "^clang-\\\\d+$", "^lld-\\\\d+$", "^llvm-\\\\d+$"]
brew = ["llvm"]
dnf = ["clang", "lld", "llvm"]
pacman = ["clang", "lld", "llvm"]

[producers."acme/node-build"]
label = "Node.js"
actions = ["actions/setup-node"]
urls = ["nodejs.org"]

[producers."acme/node-build".packages]
apk = ["nodejs", "npm"]
apt = ["nodejs", "npm"]
brew = ["node", "^node@\\\\d+(\\\\.\\\\d+)*$"]
dnf = ["nodejs", "npm"]
pacman = ["nodejs", "npm"]

[producers."acme/python-build"]
label = "CPython"
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
label = "Git"
urls = ["github.com/git/git"]

[producers."acme/mold"]
label = "mold"
urls = ["github.com/rui314/mold"]

[producers."acme/mold".packages]
apk = ["mold"]
apt = ["mold"]
brew = ["mold"]
dnf = ["mold"]
pacman = ["mold"]

[producers."acme/shck"]
label = "ShellCheck"
actions = ["ludeeus/action-shellcheck"]
urls = ["github.com/koalaman/shellcheck"]

[producers."acme/shck".packages]
apk = ["shellcheck"]
apt = ["shellcheck"]
brew = ["shellcheck"]
dnf = ["ShellCheck", "shellcheck"]
pacman = ["shellcheck"]

[producers."acme/kache"]
label = "sccache, ccache"
actions = ["mozilla-actions/sccache-action", "hendrikmuhs/ccache-action"]
urls = ["github.com/mozilla/sccache"]

[producers."acme/kache".packages]
apk = ["sccache", "ccache"]
apt = ["sccache", "ccache"]
brew = ["sccache", "ccache"]
dnf = ["sccache", "ccache"]
pacman = ["sccache", "ccache"]

[producers."acme/kache".manifests]
cargo = ["sccache"]

[producers."acme/pytest-parallel"]
label = "pytest-xdist"

[producers."acme/pytest-parallel".manifests]
pypi = ["pytest-xdist"]

[producers."acme/rustybench"]
label = "criterion, divan"

[producers."acme/rustybench".manifests]
cargo = ["criterion", "divan"]
{extra_producers}{exempt}"""


PRODUCERS = (
    "acme/gluon",
    "acme/cmake-build",
    "acme/llvm-prebuilt-musl",
    "acme/node-build",
    "acme/python-build",
    "acme/git-build",
    "acme/mold",
    "acme/shck",
    "acme/kache",
    "acme/pytest-parallel",
    "acme/rustybench",
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
    producers = {name.casefold() for name in policy.producers}
    for exemptions in policy.exempt.values():
        for exemption in exemptions:
            assert exemption.producer.casefold() in producers
            assert exemption.reason.strip()
            assert exemption.reassess.strip()


def test_rule_is_registered_with_the_python_fix() -> None:
    rule = next(rule for rule in registered_rules() if rule.id == "owned-tool-substitution")
    assert rule.fix is not None
    assert rule.commit_message is not None
    assert ".github/workflows/*.yml" in rule.allowed_paths
    assert ".github/workflows/*.yaml" in rule.allowed_paths
    assert ".github/tools.lock.json" in rule.allowed_paths


def test_producer_may_install_the_upstream_it_reproduces(project: tuple[Path, Repository, Path]) -> None:
    root, _, _ = project
    producer = Repository(RepoId.parse("acme/gluon"), ("build",))
    _write(root, "Dockerfile", "FROM alpine\nRUN apk add --no-cache meson ninja cmake\n")
    findings = owned_substitution._check(root, producer)
    assert [finding.message.split(" duplicates")[0] for finding in findings] == ["package 'cmake' installed by apk"]


def _exempt(policy: Path, repo: str, producer: str) -> None:
    (policy / "owned-substitutes.toml").write_text(
        _substitutes_text(
            exempt=(
                f'\n[exempt."{repo}".producers."{producer}"]\n'
                'reason = "The producer publishes no release for this platform."\n'
                'reassess = "Reassess when the producer ships the platform."\n'
            )
        ),
        encoding="utf-8",
    )


def test_cargo_manifest_dependencies(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(
        root,
        "Cargo.toml",
        "[package]\nname = \"demo\"\nversion = \"0.1.0\"\n\n"
        "[dependencies]\ncriterion = { version = \"0.5\", features = [\"html_reports\"] }\n\n"
        "[dev-dependencies]\ndivan = \"0.1\"\n\n"
        "[build-dependencies]\ncriterion = \"0.4\"\n\n"
        "[target.'cfg(unix)'.dependencies]\ndivan = { version = \"0.1\" }\n\n"
        "[workspace.dependencies]\nmybench = { package = \"criterion\", version = \"0.5\" }\n",
    )
    findings = owned_substitution._check(root, repository)
    producers = {finding.message.split("owned producer ")[1].split(";")[0] for finding in findings}
    assert producers == {"acme/rustybench"}
    assert all("manifest" not in finding.message for finding in findings)
    labels = [finding.message.split(" duplicates")[0] for finding in findings]
    assert any("dependency 'criterion' (cargo)" in label for label in labels)
    assert any("dependency 'divan' (cargo)" in label for label in labels)
    by_label = {
        finding.message.split(" duplicates")[0]: finding.line for finding in findings
    }
    assert by_label["dependency 'criterion' (cargo)"] == 6
    assert by_label["dependency 'divan' (cargo)"] == 9
    assert all(
        finding.message.endswith("; depend on acme/rustybench's package instead of the upstream one")
        for finding in findings
    )


def test_cargo_manifest_lookalikes_are_not_flagged(
    project: tuple[Path, Repository, Path],
) -> None:
    root, repository, _ = project
    _write(
        root,
        "crates/demo/Cargo.toml",
        "[dependencies]\n"
        "criterion-derive = \"0.3\"\n"
        "mycriterion = \"1.0\"\n"
        "divan-macros = \"0.1\"\n"
        "criterion_extra = \"0.2\"\n",
    )
    assert owned_substitution._check(root, repository) == []


def test_pyproject_and_requirements_manifests(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(
        root,
        "pyproject.toml",
        "[project]\nname = \"demo\"\nversion = \"0.1\"\n"
        "dependencies = [\n    \"requests>=2\",\n    \"pytest-xdist>=3.5\",\n]\n\n"
        "[project.optional-dependencies]\ntest = [\"pytest-xdist[psutil]\"]\n\n"
        "[dependency-groups]\ndev = [\"pytest_xdist==3.6\"]\n\n"
        "[tool.uv]\ndev-dependencies = [\"pytest-xdist\"]\n",
    )
    _write(root, "requirements-dev.txt", "# comment\n-r base.txt\npytest_xdist==3.6.1\npytest>=8\n")
    findings = owned_substitution._check(root, repository)
    assert findings
    assert all("acme/pytest-parallel" in finding.message for finding in findings)
    labels = [finding.message.split(" duplicates")[0] for finding in findings]
    assert any("dependency 'pytest-xdist' (pypi)" in label for label in labels)
    assert any("dependency 'pytest_xdist' (pypi)" in label for label in labels)
    located = {(finding.file, finding.line, finding.message.split(" duplicates")[0]) for finding in findings}
    assert ("pyproject.toml", 6, "dependency 'pytest-xdist' (pypi)") in located
    assert ("pyproject.toml", 13, "dependency 'pytest_xdist' (pypi)") in located
    assert ("requirements-dev.txt", 3, "dependency 'pytest_xdist' (pypi)") in located


def test_pip_uv_and_cargo_install_commands(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(
        root,
        ".github/workflows/ci.yml",
        "jobs:\n  test:\n    steps:\n"
        "      - run: pip install pytest-xdist==3.6\n"
        "      - run: uv add pytest-xdist\n"
        "      - run: uv pip install 'pytest-xdist[psutil]>=3'\n"
        "      - run: cargo install sccache --locked\n"
        "      - run: cargo install sccache-utils\n"
        "      - run: pip install pytest-xdist-extra\n",
    )
    findings = owned_substitution._check(root, repository)
    labels = [finding.message.split(" duplicates")[0] for finding in findings]
    assert sum("package 'pytest-xdist' installed by pip" in label for label in labels) == 1
    assert sum("package 'pytest-xdist' installed by uv add" in label for label in labels) == 1
    assert sum("package 'pytest-xdist' installed by uv pip install" in label for label in labels) == 1
    assert sum("package 'sccache' installed by cargo install" in label for label in labels) == 1
    assert all((finding.line or 0) >= 4 for finding in findings)
    assert all("instead of the upstream install" in finding.message for finding in findings)


def test_uv_pip_install_is_not_double_counted_as_pip(
    project: tuple[Path, Repository, Path],
) -> None:
    root, repository, _ = project
    _write(root, "scripts/setup.sh", "#!/bin/sh\nuv pip install pytest-xdist\n")
    findings = owned_substitution._check(root, repository)
    assert len(findings) == 1
    assert "uv pip install" in findings[0].message


def test_rustc_wrapper_assignments(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(root, "Makefile", "test:\n\tRUSTC_WRAPPER=sccache cargo test\n")
    _write(
        root,
        ".github/workflows/ci.yml",
        "jobs:\n  test:\n    env:\n      RUSTC_WRAPPER: sccache\n    steps:\n      - run: cargo test\n",
    )
    _write(root, ".cargo/config.toml", "[build]\nrustc-wrapper = \"sccache\"\n")
    _write(root, "scripts/env.sh", "#!/bin/sh\nexport RUSTC_WRAPPER=/opt/kache/bin/sccache\n")
    findings = owned_substitution._check(root, repository)
    files = {finding.file for finding in findings}
    assert files == {"Makefile", ".github/workflows/ci.yml", ".cargo/config.toml", "scripts/env.sh"}
    assert all("acme/kache" in finding.message for finding in findings)
    assert all("rustc-wrapper 'sccache'" in finding.message for finding in findings)


def test_rustc_wrapper_lookalikes(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(
        root,
        "Makefile",
        "test:\n\tRUSTC_WRAPPER=rustc cargo test\n\tRUSTC_WRAPPER=sccache-utils cargo test\n",
    )
    _write(root, ".cargo/config.toml", "[build]\nrustc-wrapper = \"sccache-wrap\"\n")
    assert owned_substitution._check(root, repository) == []


def test_shellcheck_surfaces(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(root, "Dockerfile", "RUN apt-get install -y shellcheck curl\n")
    _write(root, "scripts/dnf.sh", "#!/bin/sh\ndnf install -y ShellCheck\n")
    _write(
        root,
        ".github/workflows/lint.yml",
        "jobs:\n  lint:\n    steps:\n      - uses: ludeeus/action-shellcheck@v1\n",
    )
    _write(
        root,
        "scripts/fetch.sh",
        "#!/bin/sh\n"
        "curl -fsSL https://github.com/koalaman/shellcheck/releases/download/v0.10.0/shellcheck.tar.xz -o sc.tar.xz\n",
    )
    findings = owned_substitution._check(root, repository)
    producers = {finding.message.split("owned producer ")[1].split(";")[0] for finding in findings}
    assert producers == {"acme/shck"}
    assert len(findings) == 4


def test_shellcheck_and_kache_lookalikes(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(root, "Dockerfile", "RUN apk add shellchecks sccache-utils curl\n")
    _write(
        root,
        ".github/workflows/lint.yml",
        "jobs:\n  lint:\n    steps:\n"
        "      - uses: ludeeus/action-shellcheck-fork@v1\n"
        "      - uses: mozilla-actions/sccache-action-extra@v1\n",
    )
    _write(root, "Makefile", "test:\n\tRUSTC_WRAPPER=sccache-wrapper cargo test\n")
    assert owned_substitution._check(root, repository) == []


def test_kache_package_and_url_surfaces(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(root, "Dockerfile", "RUN apk add --no-cache sccache ccache curl\n")
    _write(
        root,
        "scripts/fetch.sh",
        "#!/bin/sh\ngit clone https://github.com/mozilla/sccache.git\n",
    )
    findings = owned_substitution._check(root, repository)
    labels = [finding.message.split(" duplicates")[0] for finding in findings]
    assert any("package 'sccache' installed by apk" in label for label in labels)
    assert any("package 'ccache' installed by apk" in label for label in labels)
    assert any("URL 'https://github.com/mozilla/sccache.git'" in label for label in labels)


def test_pypi_lookalikes(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(
        root,
        "pyproject.toml",
        "[project]\nname = \"demo\"\ndependencies = [\"pytest-xdist-extra\", \"pytest-parallel\", \"pytest\"]\n",
    )
    _write(root, "requirements.txt", "pytest_xdist_plugin==1.0\npytest-xdist-fork\n")
    assert owned_substitution._check(root, repository) == []


def test_producer_repositories_do_not_flag_their_own_manifests(
    project: tuple[Path, Repository, Path],
) -> None:
    root, _, _ = project
    _write(
        root,
        "Cargo.toml",
        "[dependencies]\ncriterion = \"0.5\"\ndivan = \"0.1\"\nsccache = \"1\"\n",
    )
    _write(root, "pyproject.toml", "[project]\ndependencies = [\"pytest-xdist\"]\n")
    _write(root, "Dockerfile", "RUN apt-get install -y shellcheck sccache\n")
    for producer in ("acme/rustybench", "acme/pytest-parallel", "acme/kache", "acme/shck"):
        repository = Repository(RepoId.parse(producer), ("build",))
        findings = owned_substitution._check(root, repository)
        own = [finding for finding in findings if producer.split("/")[1] in finding.message]
        assert own == [], producer


def test_manifest_exemptions(project: tuple[Path, Repository, Path]) -> None:
    root, repository, policy = project
    _write(root, "Cargo.toml", "[dependencies]\ncriterion = \"0.5\"\n")
    _write(root, "pyproject.toml", "[project]\ndependencies = [\"pytest-xdist\"]\n")
    _write(root, "Dockerfile", "RUN apt-get install -y shellcheck\n")
    _write(root, "Makefile", "test:\n\tRUSTC_WRAPPER=sccache cargo test\n")
    (policy / "owned-substitutes.toml").write_text(
        _substitutes_text(
            exempt=(
                '\n[exempt."acme/consumer".producers."acme/rustybench"]\n'
                'reason = "Deferred until the producer gap closes."\n'
                'reassess = "Reassess when the gap closes."\n'
                '\n[exempt."acme/consumer".producers."acme/pytest-parallel"]\n'
                'reason = "Deferred until the producer gap closes."\n'
                'reassess = "Reassess when the gap closes."\n'
                '\n[exempt."acme/consumer".producers."acme/shck"]\n'
                'reason = "Deferred until the producer gap closes."\n'
                'reassess = "Reassess when the gap closes."\n'
            )
        ),
        encoding="utf-8",
    )
    findings = owned_substitution._check(root, repository)
    assert findings
    assert all("acme/kache" in finding.message for finding in findings)
    assert any("stale exemption" not in finding.message for finding in findings)


def test_npm_manifest_ecosystem(project: tuple[Path, Repository, Path]) -> None:
    root, repository, policy = project
    (policy / "owned-tools.toml").write_text(
        _owned_tools((*PRODUCERS, "acme/npm-tool")), encoding="utf-8"
    )
    (policy / "owned-substitutes.toml").write_text(
        _substitutes_text(
            extra_producers=(
                '\n[producers."acme/npm-tool"]\n'
                'label = "left-pad"\n\n'
                '[producers."acme/npm-tool".manifests]\n'
                'npm = ["left-pad"]\n'
            ),
            exempt=(
                '\n[exempt."acme/other".producers."acme/npm-tool"]\n'
                'reason = "Not needed here."\n'
                'reassess = "Never."\n'
            ),
        ),
        encoding="utf-8",
    )
    _write(
        root,
        "package.json",
        "{\n  \"dependencies\": {\n    \"left-pad\": \"1.0.0\",\n"
        "    \"left-pad-extra\": \"2.0.0\"\n  },\n"
        "  \"devDependencies\": {\n    \"Left-Pad\": \"1.0.0\"\n  },\n"
        "  \"optionalDependencies\": {\n    \"left-pad\": \"1.0.0\"\n  }\n}\n",
    )
    findings = owned_substitution._check(root, repository)
    assert len(findings) == 1
    assert findings[0].file == "package.json"
    assert findings[0].line == 3
    assert "acme/npm-tool" in findings[0].message
    assert "dependency 'left-pad' (npm)" in findings[0].message


def test_malformed_manifests_are_skipped(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(root, "Cargo.toml", "[dependencies\ncriterion = \"0.5\"\n")
    _write(root, "pyproject.toml", "[project\ndependencies = [\"pytest-xdist\"\n")
    _write(root, "package.json", "{ not json")
    _write(root, ".cargo/config.toml", "[build\nrustc-wrapper = \"sccache\"\n")
    assert owned_substitution._check(root, repository) == []



def test_explicit_gcc_compiler_settings_are_flagged(project: tuple[Path, Repository, Path]) -> None:
    root, repository, _ = project
    _write(root, "Makefile", "CC ?= gcc\nCXX := x86_64-linux-musl-g++-14\nLD = ld\n")
    _write(root, "Dockerfile", "FROM alpine\nENV CC=gcc\nRUN cmake -DCMAKE_C_COMPILER=gcc .\n")
    _write(root, ".github/workflows/ci.yml", "jobs:\n  b:\n    env:\n      CXX: g++\n")
    _write(
        root,
        ".cargo/config.toml",
        '[target.aarch64-unknown-linux-musl]\nlinker = "aarch64-linux-musl-gcc"\n'
        '[target.x86_64-unknown-linux-musl]\nlinker = "clang"\n',
    )
    found = sorted(
        (finding.file, finding.line, finding.message.split(" duplicates")[0])
        for finding in owned_substitution._check(root, repository)
    )
    assert found == [
        (".cargo/config.toml", 2, "Cargo linker 'aarch64-linux-musl-gcc'"),
        (".github/workflows/ci.yml", 4, "compiler setting 'CXX=g++'"),
        ("Dockerfile", 2, "compiler setting 'CC=gcc'"),
        ("Dockerfile", 3, "compiler setting 'CMAKE_C_COMPILER=gcc'"),
        ("Makefile", 1, "compiler setting 'CC=gcc'"),
        ("Makefile", 2, "compiler setting 'CXX=x86_64-linux-musl-g++-14'"),
    ]


def test_generic_and_owned_compiler_settings_are_not_flagged(
    project: tuple[Path, Repository, Path],
) -> None:
    root, repository, _ = project
    _write(
        root,
        "Makefile",
        'CC ?= cc\nCXX = c++\nCC = clang\nHOSTCC = "zig cc"\nMYCC = gcc\nCCACHE=gcc-wrapper\n',
    )
    _write(root, ".cargo/config.toml", '[target.x86_64-unknown-linux-gnu]\nlinker = "cc"\n')
    assert owned_substitution._check(root, repository) == []
