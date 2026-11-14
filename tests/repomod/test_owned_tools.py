from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from repomod import owned_tools, paths
from repomod.catalog import load_catalog
from repomod.owned_tools import coverage, installer_repositories, load_owned_tools, which
from repomod.rules import rules
from repomod.types import Finding, RepoId, Repository

FOOTER = "Maintained by Joshua Li: https://github.com/acme/tool"
HEADER = (
    'version = 1\nmaintainer = "Joshua Li"\nprocedure = "https://example.invalid/owned-tools.md"\n'
    'owners = ["acme"]\ninstall_manifest = ".local/state/sync/dl-owned.verified.json"\n\n'
)


def write_policy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str) -> Path:
    path = tmp_path / "owned-tools.toml"
    path.write_text(HEADER + body, encoding="utf-8")
    monkeypatch.setattr(owned_tools, "policy_file", lambda: path)
    return path


def check(root: Path, repository: Repository) -> list[Finding]:
    rule = next(rule for rule in rules() if rule.id == "owned-tool-support")
    assert rule.applies_to.matches(repository.tags)
    return rule.check(root, repository)


def messages(findings: list[Finding]) -> list[str]:
    return [finding.message for finding in findings]


def tool_policy(command: str = 'tool = { help = { source = "src/help.rs", test = "tests/help.rs" } }') -> str:
    return f'[producers."acme/tool".commands]\n{command}\n\n[not_applicable]\n"acme/site" = "web application"\n'


def write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_policy_requires_exactly_one_support_decision(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_policy(tmp_path, monkeypatch, tool_policy('tool = { gap = "later", exempt = "never" }'))
    with pytest.raises(ValueError, match="exactly one of help, gap, or exempt"):
        load_owned_tools()


def test_policy_rejects_producers_outside_owned_namespaces(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_policy(tmp_path, monkeypatch, '[producers."other/tool".commands]\ntool = { gap = "x" }\n\n[not_applicable]\n')
    with pytest.raises(ValueError, match="outside the owned namespaces"):
        load_owned_tools()


def test_new_owned_tool_and_fork_without_coverage_are_reported(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_policy(tmp_path, monkeypatch, tool_policy())
    for tags in (("tool", "rust"), ("tool", "rust", "fork"), ("build", "python")):
        findings = check(tmp_path, Repository(RepoId("acme", "new"), tags))
        assert messages(findings) == ["missing owned-tool coverage: declare its commands or a not_applicable reason"]
        assert findings[0].file == "fleet/policy/owned-tools.toml"


def test_libraries_unowned_repositories_and_justified_exemptions_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_policy(tmp_path, monkeypatch, tool_policy())
    assert check(tmp_path, Repository(RepoId("acme", "lib"), ("library", "rust", "fork"))) == []
    assert check(tmp_path, Repository(RepoId("other", "tool"), ("tool", "rust"))) == []
    assert check(tmp_path, Repository(RepoId("acme", "site"), ("app", "typescript"))) == []


def test_tool_repositories_cannot_be_blanket_exempt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_policy(tmp_path, monkeypatch, tool_policy())
    assert messages(check(tmp_path, Repository(RepoId("acme", "site"), ("tool", "rust")))) == [
        "tool and build repositories cannot be not_applicable; declare their commands"
    ]


def test_declared_help_must_contain_the_footer_and_be_tested(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_policy(tmp_path, monkeypatch, tool_policy())
    repository = Repository(RepoId("acme", "tool"), ("tool", "rust"))
    assert messages(check(tmp_path, repository)) == [
        "tool: declared help source does not exist",
        "tool: declared help test does not exist",
    ]
    write(tmp_path, "src/help.rs", "Maintained by Joshua Li: https://github.com/acme/other\n")
    write(tmp_path, "tests/help.rs", "assert!(help.contains(\"usage\"));\n")
    assert messages(check(tmp_path, repository)) == [
        "tool: help footer names acme/other instead of acme/tool",
        "tool: help test does not check the footer's https://github.com/acme/tool link",
    ]
    write(tmp_path, "src/help.rs", "Usage: tool\n")
    assert messages(check(tmp_path, repository))[0] == f"tool: help source does not contain {FOOTER!r}"
    write(tmp_path, "src/help.rs", f"const FOOTER: &str = \"{FOOTER}\";\n")
    write(tmp_path, "tests/help.rs", "assert!(help.contains(\"https://github.com/acme/tool\"));\n")
    assert check(tmp_path, repository) == []


def test_help_identity_is_the_complete_repository_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_policy(
        tmp_path,
        monkeypatch,
        '[producers."acme/tool".commands]\ntool = { help = { source = "src/help.rs", test = "tests/help.rs" } }\n\n'
        '[producers."acme/e".commands]\ne = { help = { source = "src/help.rs", test = "tests/help.rs" } }\n\n'
        "[not_applicable]\n",
    )
    tool = Repository(RepoId("acme", "tool"), ("tool", "rust"))
    write(tmp_path, "src/help.rs", "\"Maintained by Joshua Li: https://github.com/acme/tool-old\\n\"\n")
    write(tmp_path, "tests/help.rs", "assert!(help.contains(\"https://github.com/acme/tool-old\"));\n")
    assert messages(check(tmp_path, tool)) == [
        "tool: help footer names acme/tool-old instead of acme/tool",
        "tool: help test does not check the footer's https://github.com/acme/tool link",
    ]
    e = Repository(RepoId("acme", "e"), ("tool", "rust"))
    write(tmp_path, "src/help.rs", "\"Maintained by Joshua Li: https://github.com/acme/ed\\n\"\n")
    write(tmp_path, "tests/help.rs", "assert!(help.ends_with(\"https://github.com/acme/ed\\n\"));\n")
    assert messages(check(tmp_path, e)) == [
        "e: help footer names acme/ed instead of acme/e",
        "e: help test does not check the footer's https://github.com/acme/e link",
    ]
    write(tmp_path, "src/help.rs", "\"Maintained by Joshua Li: https://github.com/acme/e\\n\"\n")
    write(tmp_path, "tests/help.rs", "assert!(help.ends_with(\"https://github.com/acme/e\\n\"));\n")
    assert check(tmp_path, e) == []


def test_gaps_are_warnings_not_successes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_policy(tmp_path, monkeypatch, tool_policy('tool = { gap = "help is generated upstream" }'))
    findings = check(tmp_path, Repository(RepoId("acme", "tool"), ("tool",)))
    assert [(finding.severity, finding.message) for finding in findings] == [
        ("warning", "tool: help integration gap: help is generated upstream")
    ]


def test_manifest_links_must_name_the_maintained_repository_or_declared_upstream(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_policy(tmp_path, monkeypatch, tool_policy('tool = { exempt = "companion" }'))
    repository = Repository(RepoId("acme", "tool"), ("tool", "rust"))
    write(tmp_path, "Cargo.toml", '[package]\nname = "tool"\nrepository = "https://github.com/old-org/tool"\n')
    write(tmp_path, "package.json", '{"repository": {"url": "git+https://github.com/acme/tool.git"}}')
    assert messages(check(tmp_path, repository)) == [
        "repository link names old-org/tool, not the maintained acme/tool"
    ]
    path = tmp_path / "owned-tools.toml"
    section = '[producers."acme/tool".commands]'
    upstream = '[producers."acme/tool"]\nupstream = "old-org/tool"\n\n'
    path.write_text(path.read_text().replace(section, upstream + section))
    assert check(tmp_path, repository) == []


INSTALLER = '''
REPO = "acme/media-build"
OTHER = "someone/else"

def install_release(prog):
    owners = {
        **{name: "acme" for name in ("tool", "short")},
        "renamed": "acme",
    }
    repo = {"short": "short-rs"}.get(prog, prog)
    url = f"https://github.com/{owners[prog]}/{repo}/releases"

def install_lz():
    fetch("https://github.com/acme/lz/releases.atom")
    fetch("https://github.com/upstream/fd/releases/latest")
'''


def test_installer_adapter_reads_owned_repository_references_statically() -> None:
    assert installer_repositories(INSTALLER, ["acme"]) == (
        RepoId("acme", "lz"),
        RepoId("acme", "media-build"),
        RepoId("acme", "renamed"),
        RepoId("acme", "short-rs"),
        RepoId("acme", "tool"),
    )


def test_consumer_must_not_install_undeclared_owned_repositories_or_commands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_policy(
        tmp_path,
        monkeypatch,
        '[producers."acme/usr"]\ninstaller = "installer.py"\nbin = ["bin"]\n\n'
        '[producers."acme/usr".commands]\ntodo = { exempt = "fixture" }\n\n'
        '[producers."acme/tool".commands]\ntool = { gap = "x" }\n\n[not_applicable]\n',
    )
    write(tmp_path, "installer.py", 'A = "acme/tool"\nB = "https://github.com/acme/renamed/releases"\n')
    for name in ("todo", "stray"):
        write(tmp_path, f"bin/{name}", "#!/bin/sh\n")
        (tmp_path / "bin" / name).chmod(0o755)
    write(tmp_path, "bin/data.txt", "not executable\n")
    assert messages(check(tmp_path, Repository(RepoId("acme", "usr"), ("config",)))) == [
        "tracked executable stray is not declared under producers.acme/usr.commands",
        "installs acme/renamed, which has no owned-tools producer; "
        "a renamed or uncatalogued repository must use its maintained name",
    ]


def catalog_file(tmp_path: Path, extra: str = "") -> Path:
    path = tmp_path / "catalog.toml"
    path.write_text(
        'version = 3\n[workspace]\nroot = "~/repos"\npersonal_owner = "acme"\n\n'
        '[repos."acme"]\ntool = ["tool", "rust"]\nlib = ["library", "rust"]\nnew = ["tool", "rust", "fork"]\n'
        'old = ["IGNORE", "tool"]\ninstalled = ["IGNORE", "tool"]\nsite = ["app"]\n' + extra,
        encoding="utf-8",
    )
    return path


def test_coverage_accounts_for_ignored_installed_and_ambiguous_tools(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_policy(
        tmp_path,
        monkeypatch,
        '[producers."acme/tool".commands]\ntool = { help = { source = "a", test = "b" } }\n\n'
        '[producers."acme/ghost".commands]\nghost = { gap = "x" }\n\n'
        '[not_applicable]\n"acme/site" = "web application"\n',
    )
    catalog = load_catalog(catalog_file(tmp_path), {"HOME": str(tmp_path)})
    entries = {
        entry.repository: (entry.state, entry.detail)
        for entry in coverage(catalog, load_owned_tools(), [RepoId("acme", "installed"), RepoId("acme", "private")])
    }
    assert entries["acme/tool"][0] == "implemented"
    assert "static" in entries["acme/tool"][1]
    assert entries["acme/ghost"] == ("error", "producer is not in fleet/catalog.toml")
    assert entries["acme/lib"] == ("not-applicable", "library without an executable")
    assert entries["acme/new"] == ("missing", "declare its commands or a not_applicable reason")
    assert entries["acme/old"] == ("not-applicable", "ignored in the catalog and not installed by usr")
    assert entries["acme/installed"] == ("missing", "usr installs it but owned-tools.toml has no producer entry")
    assert entries["acme/private"] == ("missing", "usr installs it but it is not in fleet/catalog.toml")
    assert entries["acme/site"] == ("not-applicable", "web application")


def test_coverage_reports_duplicate_commands_and_blanket_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_policy(
        tmp_path,
        monkeypatch,
        '[producers."acme/tool".commands]\ntool = { gap = "x" }\n\n'
        '[producers."acme/new".commands]\ntool = { gap = "x" }\n\n[not_applicable]\n',
    )
    catalog = load_catalog(catalog_file(tmp_path), {"HOME": str(tmp_path)})
    states = {entry.repository: entry.detail for entry in coverage(catalog, load_owned_tools())}
    assert states["acme/tool"] == "ambiguous commands: tool"
    write_policy(tmp_path, monkeypatch, '[producers."acme/tool".commands]\ntool = { gap = "x" }\n\n[not_applicable]\n')
    path = catalog_file(
        tmp_path,
        '\n[overrides."acme/tool"]\nignore = ["owned-tool-support"]\nignore_reason = "skip"\n',
    )
    catalog = load_catalog(path, {"HOME": str(tmp_path)})
    states = {entry.repository: entry.detail for entry in coverage(catalog, load_owned_tools())}
    assert states["acme/tool"] == "catalog override ignores owned-tool-support"


def git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def write_manifest(home: Path, *paths: Path) -> None:
    manifest = home / ".local/state/sync/dl-owned.verified.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    entries = {}
    for path in paths:
        kind = "D" if path.is_dir() and not path.is_symlink() else "F"
        entries[str(path)] = {"kind": kind, "fingerprint": owned_tools.manifest_fingerprint(path, kind)}
    manifest.write_text(json.dumps({"schema": 1, "entries": entries}), encoding="utf-8")


@pytest.mark.usefixtures("git_environment")
def test_which_resolves_without_executing_the_tool(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_policy(
        tmp_path,
        monkeypatch,
        '[producers."acme/tool"]\nupstream = "up/tool"\n\n'
        '[producers."acme/tool".commands]\ntool = { gap = "x" }\n'
        'rg = { gap = "x", installed_from = "up/rg" }\n\n'
        '[producers."acme/new".commands]\n'
        'new = { gap = "x", launcher_dir = ".cargo/bin", record = ".cargo/bin/.new-release" }\n'
        'dup = { gap = "x" }\n\n'
        '[producers."acme/site".commands]\ndup = { gap = "x" }\n\n[not_applicable]\n',
    )
    home = tmp_path / "home"
    workspace = tmp_path / "relocated"
    catalog = load_catalog(catalog_file(tmp_path), {"HOME": str(home), "REPOMOD_ROOT": str(workspace)})
    policy = load_owned_tools()
    marker = tmp_path / "executed"
    managed = home / ".local/bin"
    managed.mkdir(parents=True)
    other = tmp_path / "other-bin"
    other.mkdir()
    for directory in (managed, other):
        for name in ("tool", "rg"):
            executable = directory / name
            executable.write_text(f"#!/bin/sh\ntouch {marker}\nexit 1\n", encoding="utf-8")
            executable.chmod(0o755)
    environ = {"HOME": str(home), "PATH": f"{managed}{os.pathsep}{other}"}

    assert which("nothing", catalog, policy, environ)["status"] == "unknown"
    assert which("dup", catalog, policy, environ) == {
        "command": "dup",
        "status": "ambiguous",
        "producers": ["acme/new", "acme/site"],
    }

    result = which("tool", catalog, policy, environ)
    assert result["status"] == "missing-checkout"
    assert result["checkout"] == {"state": "missing", "path": str(workspace / "tool")}
    assert result["upstream"] == "up/tool"

    checkout = workspace / "tool"
    checkout.mkdir(parents=True)
    git("init", "-q", cwd=checkout)
    git("remote", "add", "origin", "git@github.com:other/tool.git", cwd=checkout)
    assert which("tool", catalog, policy, environ)["status"] == "origin-mismatch"
    git("remote", "set-url", "origin", "https://github.com/acme/tool.git", cwd=checkout)

    result = which("tool", catalog, policy, environ)
    assert result["status"] == "unverified"
    assert result["executable"]["path"] == str(managed / "tool")
    assert result["executable"]["detail"].startswith("no install manifest")

    state = home / ".local/state/dl"
    state.mkdir(parents=True)
    (state / "tool").write_text("not-a-release-or-sha\n", encoding="utf-8")
    assert which("tool", catalog, policy, environ)["status"] == "unverified"

    write_manifest(home, managed / "tool", managed / "rg")
    (state / "tool").write_text(f"release-{'a' * 40}:etag\n", encoding="utf-8")
    result = which("tool", catalog, policy, environ)
    assert result["status"] == "owned"
    assert result["executable"]["evidence"] == "installer-manifest"
    assert result["executable"]["revision"] == f"release-{'a' * 40}"
    (state / "tool").write_text("etag-only\n", encoding="utf-8")
    assert which("tool", catalog, policy, environ)["executable"]["revision"] is None

    (managed / "tool").write_text(f"#!/bin/sh\ntouch {marker}\nexit 2\n", encoding="utf-8")
    result = which("tool", catalog, policy, environ)
    assert result["status"] == "unverified"
    assert result["executable"]["detail"] == f"{managed / 'tool'} changed since it was installed"

    assert which("rg", catalog, policy, environ)["status"] == "upstream-install"

    shadowed = {"HOME": str(home), "PATH": f"{other}{os.pathsep}{managed}"}
    assert which("tool", catalog, policy, shadowed)["status"] == "shadowed"

    new_checkout = workspace / "new"
    new_checkout.mkdir(parents=True)
    git("init", "-q", cwd=new_checkout)
    git("remote", "add", "origin", "git@github.com:acme/new.git", cwd=new_checkout)
    assert which("new", catalog, policy, environ)["status"] == "not-installed"
    cargo_bin = home / ".cargo/bin"
    cargo_bin.mkdir(parents=True)
    (cargo_bin / "new").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    (cargo_bin / "new").chmod(0o755)
    cargo_environ = {"HOME": str(home), "PATH": str(cargo_bin)}
    record = cargo_bin / ".new-release"
    record.write_text("not-a-release-or-sha\n", encoding="utf-8")
    assert which("new", catalog, policy, cargo_environ)["status"] == "unverified"
    digest = hashlib.sha256((cargo_bin / "new").read_bytes()).hexdigest()
    record.write_text(f"release-{'b' * 40}\n{digest}  new\n", encoding="utf-8")
    result = which("new", catalog, policy, cargo_environ)
    assert result["status"] == "owned"
    assert result["executable"]["revision"] == f"release-{'b' * 40}"
    (cargo_bin / "new").write_text("#!/bin/sh\nexit 3\n", encoding="utf-8")
    assert which("new", catalog, policy, cargo_environ)["status"] == "unverified"

    assert not marker.exists()
    assert not any((checkout / ".git").glob("index.lock"))


@pytest.mark.usefixtures("git_environment")
def test_which_verifies_source_links_and_release_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_policy(tmp_path, monkeypatch, '[producers."acme/tool".commands]\ntool = { gap = "x" }\n\n[not_applicable]\n')
    home = tmp_path / "home"
    workspace = tmp_path / "workspace"
    catalog = load_catalog(catalog_file(tmp_path), {"HOME": str(home), "REPOMOD_ROOT": str(workspace)})
    policy = load_owned_tools()
    checkout = workspace / "tool"
    clone = tmp_path / "clone"
    for path in (checkout, clone):
        path.mkdir(parents=True)
        git("init", "-q", cwd=path)
        git("remote", "add", "origin", "git@github.com:acme/tool.git", cwd=path)
    script = clone / "bin/tool"
    script.parent.mkdir()
    script.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    script.chmod(0o755)
    git("add", "bin/tool", cwd=clone)
    git("commit", "-qm", "tool", cwd=clone)
    managed = home / ".local/bin"
    managed.mkdir(parents=True)
    (managed / "tool").symlink_to(script)
    environ = {"HOME": str(home), "PATH": str(managed)}

    result = which("tool", catalog, policy, environ)
    assert result["status"] == "owned"
    assert result["executable"]["evidence"] == "source-link"
    assert result["executable"]["work_tree"] == str(clone.resolve())
    assert result["executable"]["revision"] == subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=clone, check=True, capture_output=True, text=True
    ).stdout.strip()

    script.write_text("#!/bin/sh\nexit 2\n", encoding="utf-8")
    result = which("tool", catalog, policy, environ)
    assert result["status"] == "owned"
    assert result["executable"]["revision"] is None
    assert result["executable"]["detail"].endswith("differs from HEAD")

    git("remote", "set-url", "origin", "git@github.com:other/tool.git", cwd=clone)
    assert which("tool", catalog, policy, environ)["status"] == "unverified"

    release = home / ".local/share/tool/releases/not-a-revision"
    (release / "bin").mkdir(parents=True)
    binary = release / "bin/tool"
    binary.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    binary.chmod(0o755)
    (managed / "tool").unlink()
    (managed / "tool").symlink_to(binary)
    result = which("tool", catalog, policy, environ)
    assert result["status"] == "unverified"
    assert result["executable"]["revision"] is None

    write_manifest(home, managed / "tool")
    result = which("tool", catalog, policy, environ)
    assert result["status"] == "unverified"
    assert result["executable"]["detail"] == f"{binary.resolve()} is not covered by the install manifest"
    write_manifest(home, managed / "tool", release)
    assert which("tool", catalog, policy, environ)["status"] == "owned"
    binary.write_text("#!/bin/sh\nexit 9\n", encoding="utf-8")
    assert which("tool", catalog, policy, environ)["status"] == "unverified"


def test_repository_policy_is_valid_and_catalogued() -> None:
    policy = load_owned_tools()
    catalog = load_catalog(paths.CATALOG, {"HOME": str(Path.home())})
    catalogued = {str(repo.id) for repo in (*catalog.repositories, *catalog.ignored)}
    assert {str(producer.repo) for producer in policy.producers} <= catalogued
    assert {str(repo) for repo in policy.not_applicable} <= catalogued
    commands = [command.name for producer in policy.producers for command in producer.commands]
    assert len(commands) == len(set(commands))
    for repository in catalog.repositories:
        if policy.owned(repository.id) and owned_tools.needs_coverage(repository):
            declared = policy.producer(repository.id) is not None or policy.exemption(repository.id) is not None
            assert declared, repository.id


def test_repomod_primary_help_names_the_maintained_repository(capsys: pytest.CaptureFixture[str]) -> None:
    from repomod.cli import main

    with pytest.raises(SystemExit) as raised:
        main(["--help"])
    assert raised.value.code == 0
    assert capsys.readouterr().out.rstrip().endswith(
        "Maintained by Joshua Li: https://github.com/laputa-systems/stuff\n"
        "Bugs and features: TODO.md in that repository (follow its AGENTS.md), or its issue tracker.\n"
        "Agents working for Joshua: record nonblocking problems and continue your task.\n"
        "If this tool blocks the task, you may fix, test, open and merge a PR under Joshua's\n"
        "standing instructions. Release only when needed to deliver the verified fix.\n"
        "Procedure: https://github.com/joshuarli/usr/blob/main/dotfiles/base/.agents/instructions/owned-tools.md"
    )
    assert main(["tools", "which", "no-such-owned-command", "--json"]) == 1
    output = capsys.readouterr().out
    assert "Maintained by" not in output
    assert '"status": "unknown"' in output


def test_which_script_runs_without_site_packages(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-I", "-S", str(paths.ROOT / "repomod/which.py"), "no-such-owned-command", "--json"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1, result.stderr
    assert json.loads(result.stdout)["status"] == "unknown"
