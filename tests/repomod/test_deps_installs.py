from __future__ import annotations

from repomod import install_parse
from repomod.dependencies.adapters.installs import InstallsAdapter
from repomod.dependencies.model import (
    AdapterResult,
    Ecosystem,
    InputContent,
    Relation,
    Resolution,
    Scope,
    purl,
)


def _extract(files: dict[str, str]) -> AdapterResult:
    return InstallsAdapter().extract(
        tuple(InputContent(path, text) for path, text in files.items())
    )


def _purls(result: AdapterResult) -> set[str]:
    return {instance.purl for instance in result.instances}


def test_system_package_installs_become_components() -> None:
    result = _extract(
        {
            ".github/workflows/ci.yml": (
                "jobs:\n"
                "  build:\n"
                "    steps:\n"
                "      - run: apt-get update && apt-get install -y git curl \\\n"
                "          python3\n"
            ),
            "scripts/setup.sh": (
                "apk add --no-cache git\n"
                "pacman -S --noconfirm mold\n"
                "brew install cmake\n"
            ),
            "Makefile": "all:\n\tapt-get install -y jq\n",
        }
    )

    assert _purls(result) == {
        purl(Ecosystem.SYSTEM, "apt/git"),
        purl(Ecosystem.SYSTEM, "apt/curl"),
        purl(Ecosystem.SYSTEM, "apt/python3"),
        purl(Ecosystem.APK, "git"),
        purl(Ecosystem.SYSTEM, "pacman/mold"),
        purl(Ecosystem.SYSTEM, "brew/cmake"),
        purl(Ecosystem.SYSTEM, "apt/jq"),
    }
    for edge in result.edges:
        assert edge.relation is Relation.DIRECT
        assert edge.scope is Scope.SYSTEM
        assert edge.resolution is Resolution.DECLARED_ONLY


def test_dockerfile_apk_is_left_to_the_containers_adapter() -> None:
    adapter = InstallsAdapter()
    dockerfile = "Dockerfile"
    assert adapter.matches(dockerfile)
    result = adapter.extract(
        (InputContent(dockerfile, "RUN apk add git\nRUN apt-get install -y curl\n"),)
    )

    assert _purls(result) == {purl(Ecosystem.SYSTEM, "apt/curl")}


def test_install_surfaces_match_the_rule() -> None:
    adapter = InstallsAdapter()
    assert adapter.matches(".github/workflows/ci.yaml")
    assert adapter.matches("sub/dir/Makefile")
    assert adapter.matches("tools/build.mk")
    assert adapter.matches("flake.nix")
    assert adapter.matches("docker/Dockerfile")
    assert adapter.matches("scripts/deploy.sh")
    assert adapter.matches("docker/proxy.conf")
    assert not adapter.matches("Cargo.toml")
    assert not adapter.matches("pyproject.toml")
    assert not adapter.matches("package.json")
    assert not adapter.matches("tests/scripts/install.sh")
    assert not adapter.matches("docs/scripts/install.sh")
    assert not adapter.matches("src/main.rs")


def test_assignments_and_continuations_expand() -> None:
    text = "PKGS=git curl\napt-get install -y $PKGS \\\n    python3\n"
    env = install_parse.assignments(text)
    _number, line = install_parse.logical_lines(text)[1]
    installs = install_parse.system_package_installs(line, env)
    assert installs == [
        ("apt", "git"),
        ("apt", "curl"),
        ("apt", "python3"),
    ]
