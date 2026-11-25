from __future__ import annotations

import os
from pathlib import Path

import pytest

from repomod.dependencies import commands
from repomod.rules import shell_portability
from repomod.types import RepoId, Repository

FIXTURES = Path(__file__).parent / "fixtures" / "shell_portability"
AST_GREP = os.environ.get("REPOMOD_AST_GREP")
REPO = Repository(RepoId("acme", "demo"), ())

AUDIT_SCRIPT = """\
#!/bin/sh
shasum -a 256 file
md5 file
md5sum file
nproc
flock /tmp/lock -c true
getopt -o ab file
tac file
which git
stat -c %s file
stat -f file
sed -i 's/a/b/' file
sed -i.bak 's/a/b/' file
grep -P 'pat' file
grep '\\s' file
grep -E 'a\\|b' file
sed 's/\\w/x/g' file
sed 's/a\\+b/c/' file
sed 's/a\\?b/c/' file
date -d tomorrow +%s
date -j 100
date -v+1d
date +%N
find . -printf '%p\\n'
find . -regextype posix-extended -name x
sort -V file
du -b file
readlink -e link
readlink -m link
cp --reflink=auto a b
cp -T a b
mv -T a b
ln -r a b
install -D a /dst
tail -r file
echo -e 'x'
echo -n 'x'
openssl dgst -sha256 file
sysctl -n hw.ncpu
sha256sum file
sed -E 's/a/b/' file
grep -E 'pat' file
printf '%s\\n' x
stat file
echo "shasum is only mentioned here"
"""

CASES: dict[str, list[commands.SurfaceFile]] = {
    "audit": [
        commands.SurfaceFile("scripts/audit.sh", commands.KIND_SHELL, AUDIT_SCRIPT)
    ],
    "lines": [
        commands.SurfaceFile(
            "scripts/deep.sh",
            commands.KIND_SHELL,
            "#!/bin/sh\n"
            "true\n"
            "if true; then\n"
            "  shasum -a 256 nested/file\n"
            "fi\n"
            "stat -c %s other\n",
        )
    ],
    "workflow": [
        commands.SurfaceFile(
            ".github/workflows/ci.yml",
            commands.KIND_WORKFLOW,
            "name: ci\n"
            "on: [push]\n"
            "jobs:\n"
            "  fixed:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - run: |\n"
            "          shasum -a 256 x\n"
            "  matrix:\n"
            "    runs-on: ${{ matrix.os }}\n"
            "    steps:\n"
            "      - run: stat -c %s f\n",
        )
    ],
    "makefile": [
        commands.SurfaceFile(
            "Makefile",
            commands.KIND_MAKEFILE,
            "all: deps\n"
            "\t@echo building\n"
            "\tshasum -a 256 dist/app\n"
            "\tcp -T dist/app /out/\n",
        )
    ],
    "dockerfile": [
        commands.SurfaceFile(
            "Dockerfile",
            commands.KIND_DOCKERFILE,
            "FROM alpine:3.20\n"
            "RUN apk add --no-cache make \\\n"
            "    && shasum -a 256 /src\n",
        )
    ],
}


def _sites(case: str) -> tuple[commands.CallSite, ...]:
    assembly = commands.assemble(CASES[case])
    data = (FIXTURES / f"{case}.json").read_bytes()
    return commands.sites(assembly, commands.matches_from_json(data))


def _site(
    name: str,
    arguments: tuple[str, ...] = (),
    *,
    path: str = "scripts/tool.sh",
    kind: str = commands.KIND_SHELL,
    line: int = 3,
) -> commands.CallSite:
    return commands.CallSite(path, kind, line, name, arguments)


def _file(
    path: str = "scripts/tool.sh",
    kind: str = commands.KIND_SHELL,
    text: str = "#!/bin/sh\ntrue\n",
) -> commands.SurfaceFile:
    return commands.SurfaceFile(path, kind, text)


def _evaluate(
    files: list[commands.SurfaceFile], sites: list[commands.CallSite]
) -> list[str]:
    policy = shell_portability._load_policy()
    findings = shell_portability._evaluate(REPO, policy, files, sites)
    return [finding.message for finding in findings]


def test_syntax_only() -> None:
    for name in CASES:
        _sites(name)


def test_shell_call_sites_carry_path_line_name_and_arguments() -> None:
    sites = _sites("lines")
    assert [
        (site.name, site.line, site.arguments)
        for site in sites
        if site.name in {"shasum", "stat"}
    ] == [
        ("shasum", 4, ("-a", "256", "nested/file")),
        ("stat", 6, ("-c", "%s", "other")),
    ]
    assert {site.path for site in sites} == {"scripts/deep.sh"}
    assert {site.kind for site in sites} == {commands.KIND_SHELL}


def test_workflow_call_sites_and_run_block_lines() -> None:
    sites = _sites("workflow")
    assert [(site.name, site.line, site.arguments) for site in sites] == [
        ("shasum", 8, ("-a", "256", "x")),
        ("stat", 12, ("-c", "%s", "f")),
    ]
    assert {site.kind for site in sites} == {commands.KIND_WORKFLOW}


def test_makefile_call_sites() -> None:
    sites = _sites("makefile")
    assert [(site.name, site.line, site.arguments) for site in sites] == [
        ("echo", 2, ("building",)),
        ("shasum", 3, ("-a", "256", "dist/app")),
        ("cp", 4, ("-T", "dist/app", "/out/")),
    ]
    assert {site.kind for site in sites} == {commands.KIND_MAKEFILE}


def test_dockerfile_call_sites() -> None:
    sites = _sites("dockerfile")
    assert [(site.name, site.line, site.arguments) for site in sites] == [
        ("apk", 2, ("add", "--no-cache", "make")),
        ("shasum", 2, ("-a", "256", "/src")),
    ]
    assert {site.kind for site in sites} == {commands.KIND_DOCKERFILE}


def test_fixture_covers_every_policy_command() -> None:
    sites = _sites("audit")
    policy = shell_portability._load_policy()
    names = {site.name for site in sites}
    for rule in policy.rules:
        assert rule.commands & names, f"no fixture site for {sorted(rule.commands)}"


def test_fixture_produces_a_finding_for_every_policy_rule() -> None:
    files = CASES["audit"]
    sites = _sites("audit")
    policy = shell_portability._load_policy()
    findings = shell_portability._evaluate(REPO, policy, files, sites)
    messages = [finding.message for finding in findings]
    for rule in policy.rules:
        assert any(rule.use in message for message in messages), (
            f"no finding carries the replacement for {sorted(rule.commands)}"
        )


def test_findings_name_file_line_and_replacement() -> None:
    files = [_file()]
    sites = [_site("shasum", ("-a", "256", "x"), line=3)]
    findings = shell_portability._evaluate(REPO, shell_portability._load_policy(), files, sites)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.file == "scripts/tool.sh"
    assert finding.line == 3
    assert finding.rule == "shell-portability"
    assert finding.kind == "violation"
    assert "shasum" in finding.message
    assert "sha256sum" in finding.message


@pytest.mark.parametrize(
    ("name", "arguments", "expected"),
    [
        ("shasum", ("-a", "256"), "sha256sum"),
        ("md5", ("file",), "sha256sum"),
        ("md5sum", ("file",), "sha256sum"),
        ("nproc", (), "getconf _NPROCESSORS_ONLN"),
        ("flock", ("/tmp/l"), "mkdir lock directory"),
        ("getopt", ("-o", "ab"), "getopts"),
        ("tac", ("file",), "awk to reverse"),
        ("which", ("git",), "command -v"),
        ("stat", ("-c", "%s"), "wc -c"),
        ("stat", ("-f", "file"), "find FILE -newer REF"),
        ("sed", ("-i", "s/a/b/"), "temp file"),
        ("sed", ("-i.bak", "s/a/b/"), "temp file"),
        ("sed", ("--in-place", "s/a/b/"), "temp file"),
        ("grep", ("-P", "pat"), "grep -E"),
        ("grep", ("--perl-regexp", "pat"), "grep -E"),
        ("date", ("-d", "tomorrow"), "date -u +%s"),
        ("date", ("--date", "tomorrow"), "date -u +%s"),
        ("date", ("-j", "100"), "date -u +%s"),
        ("date", ("-v+1d",), "date -u +%s"),
        ("date", ("+%N",), "date -u +%s"),
        ("find", ("-printf", "%p"), "POSIX find"),
        ("find", ("-regextype", "gnu"), "POSIX find"),
        ("sort", ("-V",), "POSIX sort"),
        ("sort", ("--version-sort",), "POSIX sort"),
        ("du", ("-b",), "wc -c"),
        ("du", ("--bytes",), "wc -c"),
        ("readlink", ("-e",), "readlink -f"),
        ("readlink", ("-m",), "readlink -f"),
        ("cp", ("--reflink=auto", "a", "b"), "cp -a"),
        ("cp", ("-T", "a", "b"), "cp -a"),
        ("mv", ("-T", "a", "b"), "POSIX mv"),
        ("ln", ("-r", "a", "b"), "ln -sfn"),
        ("install", ("-D", "a", "b"), "mkdir -p"),
        ("tail", ("-r", "f"), "awk to reverse"),
        ("echo", ("-e", "x"), "printf"),
        ("echo", ("-n", "x"), "printf"),
        ("openssl", ("dgst", "-sha256"), "sha256sum"),
        ("sysctl", ("-n", "hw.ncpu"), "getconf _NPROCESSORS_ONLN"),
        ("sed", ("s/\\s/_/g",), "[[:space:]]"),
        ("grep", ("a\\|b",), "[[:alnum:]_]"),
        ("grep", ("\\w+",), "[[:alnum:]_]"),
        ("sed", ("s/a\\+b/c/",), "[[:alnum:]_]"),
        ("sed", ("s/a\\?b/c/",), "[[:alnum:]_]"),
    ],
)
def test_forbidden_command_and_option(name: str, arguments: tuple[str, ...], expected: str) -> None:
    messages = _evaluate([_file()], [_site(name, arguments)])
    assert messages, f"{name} {arguments} produced no finding"
    assert any(expected in message for message in messages), messages


@pytest.mark.parametrize(
    ("name", "arguments"),
    [
        ("sha256sum", ("file",)),
        ("getopts", ("x",)),
        ("sed", ("-E", "s/a/b/")),
        ("grep", ("-E", "pat")),
        ("printf", ("%s", "x")),
        ("command", ("-v", "git")),
        ("stat", ("file",)),
        ("stat", ("-t", "%Y", "file")),
        ("echo", ("shasum",)),
        ("echo", ("-name",)),
        ("cp", ("-a", "src", "dst")),
        ("find", (".", "-name", "x")),
        ("date", ("-u", "+%s")),
        ("date", ("-u", "+%Y-%m-%dT%H:%M:%SZ")),
        ("openssl", ("list", "-digest-algorithms")),
        ("sysctl", ("kern.hostname",)),
        ("tail", ("-n", "+5", "f")),
        ("du", ("-h",)),
        ("readlink", ("-f",)),
        ("sort", ("-k2",)),
        ("sed", ("s/[|]/x/g",)),
    ],
)
def test_lookalikes_are_not_flagged(name: str, arguments: tuple[str, ...]) -> None:
    assert _evaluate([_file()], [_site(name, arguments)]) == []


def test_double_dash_stops_option_matching() -> None:
    messages = _evaluate([_file()], [_site("grep", ("--", "-P"))])
    assert messages == []
    messages = _evaluate([_file()], [_site("stat", ("--", "-c"))])
    assert messages == []


def test_platform_directory_exemptions() -> None:
    for directory in ("darwin", "macos", "linux", "alpine"):
        path = f"dotfiles/{directory}/setup.sh"
        assert _evaluate(
            [_file(path)], [_site("shasum", ("f",), path=path)]
        ) == []


def test_platform_filename_exemptions() -> None:
    for name in ("tool_linux.sh", "tool_darwin.py", "tool_macos.rs", "tool-linux", "tool-macos"):
        path = f"scripts/{name}"
        assert _evaluate(
            [_file(path)], [_site("shasum", ("f",), path=path)]
        ) == []


def test_dockerfile_kind_is_exempt() -> None:
    path = "docker/Dockerfile"
    assert _evaluate(
        [_file(path, commands.KIND_DOCKERFILE)],
        [_site("shasum", ("f",), path=path, kind=commands.KIND_DOCKERFILE)],
    ) == []


def test_workflow_fixed_runs_on_is_exempt_but_matrix_is_not() -> None:
    text = (
        "jobs:\n"
        "  fixed:\n"
        "    runs-on: macos-15\n"
        "    steps:\n"
        "      - run: |\n"
        "          shasum x\n"
        "  matrix:\n"
        "    runs-on: ${{ matrix.os }}\n"
        "    steps:\n"
        "      - run: |\n"
        "          shasum y\n"
    )
    files = [_file(".github/workflows/ci.yml", commands.KIND_WORKFLOW, text)]
    sites = [
        _site("shasum", ("x",), path=".github/workflows/ci.yml",
              kind=commands.KIND_WORKFLOW, line=6),
        _site("shasum", ("y",), path=".github/workflows/ci.yml",
              kind=commands.KIND_WORKFLOW, line=11),
    ]
    findings = shell_portability._evaluate(
        REPO, shell_portability._load_policy(), files, sites
    )
    assert [(finding.line, finding.message.split()[0]) for finding in findings] == [
        (11, "shasum")
    ]


def test_workflow_runs_on_list_spanning_oses_is_not_exempt() -> None:
    text = (
        "jobs:\n"
        "  multi:\n"
        "    runs-on: [ubuntu-latest, macos-latest]\n"
        "    steps:\n"
        "      - run: shasum x\n"
    )
    files = [_file(".github/workflows/ci.yml", commands.KIND_WORKFLOW, text)]
    sites = [
        _site("shasum", ("x",), path=".github/workflows/ci.yml",
              kind=commands.KIND_WORKFLOW, line=5)
    ]
    findings = shell_portability._evaluate(
        REPO, shell_portability._load_policy(), files, sites
    )
    assert len(findings) == 1


def test_policy_loads_and_validates() -> None:
    policy = shell_portability._load_policy()
    assert policy.rules
    assert all(rule.use for rule in policy.rules)
    assert all(item.reason and item.reassess for item in policy.exempt.values())


_ORIGINAL_LOAD_POLICY = shell_portability._load_policy


def _exempt_policy() -> shell_portability.Policy:
    return shell_portability.Policy(
        _ORIGINAL_LOAD_POLICY().rules,
        {"acme/demo": shell_portability.Exemption("acme/demo", "reason", "reassess")},
    )


def test_check_reports_stale_exemption(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shell_portability, "_load_policy", _exempt_policy)
    monkeypatch.setattr(
        shell_portability.commands_module, "call_sites", lambda files: ()
    )
    findings = shell_portability._check(tmp_path, REPO)
    assert [finding.message for finding in findings if "stale exemption" in finding.message]


def test_check_suppresses_exempt_repository_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(shell_portability, "_load_policy", _exempt_policy)
    site = _site("shasum", ("f",))
    monkeypatch.setattr(
        shell_portability.commands_module, "call_sites", lambda files: (site,)
    )
    findings = shell_portability._check(tmp_path, REPO)
    assert findings == []


def _path_exempt_policy() -> shell_portability.Policy:
    return shell_portability.Policy(
        _ORIGINAL_LOAD_POLICY().rules,
        {
            "acme/demo": shell_portability.Exemption(
                "acme/demo", "reason", "reassess", ("corpus/files/*",)
            )
        },
    )


def test_path_exemption_suppresses_only_matching_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(shell_portability, "_load_policy", _path_exempt_policy)
    sites = (_site("shasum", ("f",), path="corpus/files/a.sh"), _site("shasum", ("f",), path="scripts/real.sh"))
    monkeypatch.setattr(shell_portability.commands_module, "call_sites", lambda files: sites)
    findings = shell_portability._check(tmp_path, REPO)
    assert [finding.file for finding in findings] == ["scripts/real.sh"]


def test_path_exemption_matching_nothing_is_stale(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(shell_portability, "_load_policy", _path_exempt_policy)
    sites = (_site("shasum", ("f",), path="scripts/real.sh"),)
    monkeypatch.setattr(shell_portability.commands_module, "call_sites", lambda files: sites)
    messages = [finding.message for finding in shell_portability._check(tmp_path, REPO)]
    assert any("stale exemption" in message for message in messages)
    assert any("shasum" in message for message in messages)


@pytest.mark.skipif(AST_GREP is None, reason="REPOMOD_AST_GREP is not set")
def test_real_ast_grep_call_sites() -> None:
    files = CASES["lines"] + CASES["workflow"] + CASES["makefile"] + CASES["dockerfile"]
    sites = commands.call_sites(files)
    assert ("shasum", "scripts/deep.sh", 4) in {
        (site.name, site.path, site.line) for site in sites
    }
    assert ("shasum", ".github/workflows/ci.yml", 8) in {
        (site.name, site.path, site.line) for site in sites
    }
