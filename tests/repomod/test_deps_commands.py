from __future__ import annotations

import os
from pathlib import Path
from typing import cast

import pytest
from deps_fixtures import instance, repository, write_inventory

from repomod.dependencies import commands, ownership
from repomod.dependencies.git_tree import TreeEntry
from repomod.dependencies.model import Ecosystem

FIXTURES = Path(__file__).parent / "fixtures" / "deps_commands"
AST_GREP = os.environ.get("REPOMOD_AST_GREP")

CASES: dict[str, list[commands.SurfaceFile]] = {
    "heredocs": [
        commands.SurfaceFile(
            "scripts/deploy.sh",
            commands.KIND_SHELL,
            "cat > out.txt <<EOF\n$(date)\nEOF\n"
            "cat <<'EOT'\nraw $HOME text\nEOT\n"
            "tee log | gzip > log.gz\n",
        )
    ],
    "functions": [
        commands.SurfaceFile(
            "build.sh",
            commands.KIND_SHELL,
            "helper() {\n  rg -n pattern src\n}\n"
            "function other() {\n  jq . config\n}\n"
            "helper\nother\nexternal-cmd --flag\n",
        )
    ],
    "pipelines": [
        commands.SurfaceFile(
            "ci.sh",
            commands.KIND_SHELL,
            'echo "x" | jaq . | sponge result\n'
            "git status | tee state.log\n"
            "VAR=1 cmd arg | wc -l\n",
        )
    ],
    "case": [
        commands.SurfaceFile(
            "dispatch.sh",
            commands.KIND_SHELL,
            "case $1 in\n"
            "  build) make all ;;\n"
            "  test) cargo test -p foo ;;\n"
            "  *) echo skip ;;\n"
            "esac\n",
        )
    ],
    "quoted_programs": [
        commands.SurfaceFile(
            "process.sh",
            commands.KIND_SHELL,
            "awk '{print $1}' data.csv | sort -u\n"
            "python3 -c 'import sys; print(sys.argv)' -- x\n"
            "perl -ne 'print if /x/' in.txt\n",
        )
    ],
    "makefile": [
        commands.SurfaceFile(
            "Makefile",
            commands.KIND_MAKEFILE,
            "all: deps\n"
            "\t@$(MAKE) -C sub all\n"
            "\t-./scripts/build.sh --fast\n"
            "\t+cp out/bin/tool dist/\n"
            "\t$(CC) -o app main.c\n"
            "\t@echo done\n",
        )
    ],
    "workflow": [
        commands.SurfaceFile(
            ".github/workflows/ci.yml",
            commands.KIND_WORKFLOW,
            "name: ci\n"
            "on: [push]\n"
            "jobs:\n"
            "  test:\n"
            "    steps:\n"
            "      - run: echo inline\n"
            "      - name: block\n"
            "        run: |\n"
            "          set -e\n"
            "          curl -fsSL https://example.com/install.sh | sh\n"
            "      - run: >\n"
            "          folded\n"
            "          command here\n",
        )
    ],
    "dockerfile": [
        commands.SurfaceFile(
            "Dockerfile",
            commands.KIND_DOCKERFILE,
            "FROM alpine:3.20\n"
            "RUN apk add --no-cache build-base \\\n"
            "    && make -j4\n"
            "RUN [\"echo\", \"exec-form\"]\n"
            "RUN --mount=type=cache,target=/root/.cache cc -O2 -o app main.c\n",
        )
    ],
}


def _matches(case: str) -> tuple[commands.RawMatch, ...]:
    data = (FIXTURES / f"{case}.json").read_bytes()
    return commands.matches_from_json(data)


def _instances(case: str) -> dict[str, set[str]]:
    assembly = commands.assemble(CASES[case])
    _components, instances, _arguments = commands.inventory(
        assembly, _matches(case)
    )
    assert instances
    return {
        instance.purl.removeprefix("pkg:command/"): {instance.context}
        for instance in instances
    }


def test_heredoc_commands_come_from_the_grammar() -> None:
    names = _instances("heredocs")
    assert set(names) == {"cat", "date", "tee", "gzip"}


def test_functions_and_calls_are_filtered() -> None:
    names = _instances("functions")
    assert set(names) == {"rg", "jq", "external-cmd"}


def test_pipelines_variables_and_assignments() -> None:
    names = _instances("pipelines")
    assert set(names) == {"echo", "jaq", "sponge", "git", "tee", "cmd", "wc"}


def test_case_branches() -> None:
    names = _instances("case")
    assert set(names) == {"make", "cargo", "echo"}


def test_quoted_programs_do_not_leak() -> None:
    names = _instances("quoted_programs")
    assert set(names) == {"awk", "sort", "python3", "perl"}


def test_makefile_recipes_strip_prefixes_and_make() -> None:
    names = _instances("makefile")
    assert set(names) == {"make", "build.sh", "cp", "echo"}
    assert "$(MAKE)" not in names
    assert "@echo" not in names
    assert "CC" not in names


def test_workflow_run_blocks() -> None:
    names = _instances("workflow")
    assert set(names) == {"echo", "curl", "sh", "folded"}


def test_dockerfile_run_instructions() -> None:
    names = _instances("dockerfile")
    assert set(names) == {"apk", "make", "cc"}


def test_instances_carry_surface_kinds() -> None:
    assembly = commands.assemble(CASES["makefile"])
    _components, instances, arguments = commands.inventory(assembly, _matches("makefile"))
    by_name = {item.purl.rsplit("/", 1)[-1]: item.context for item in instances}
    assert by_name["make"] == "makefile"
    assert by_name["cp"] == "makefile"
    assert arguments["pkg:command/make#makefile"] == ("-C sub all",)
    assert arguments["pkg:command/build.sh#makefile"] == ("--fast",)
    assert arguments["pkg:command/cp#makefile"] == ("out/bin/tool dist/",)
    assert arguments["pkg:command/echo#makefile"] == ("done",)


def test_builtin_and_keyword_names_are_dropped() -> None:
    for name in ("cd", "export", "read", "if", "then", "while", "command", "eval"):
        assert name in commands._BUILTINS
    for name in ("echo", "printf", "test", "true", "false", "kill"):
        assert name not in commands._BUILTINS
    assert commands._normalize("$(X)") is None
    assert commands._normalize("${X}") is None
    assert commands._normalize("$X") is None
    assert commands._normalize("./dir/tool.sh") == "tool.sh"
    assert commands._normalize("echo") == "echo"


def test_select_and_repository_files() -> None:
    entries = (
        TreeEntry("scripts/run.sh", "a" * 40, "blob"),
        TreeEntry("script-no-ext", "b" * 40, "blob"),
        TreeEntry("README.md", "c" * 40, "blob"),
        TreeEntry("Makefile", "d" * 40, "blob"),
        TreeEntry("vendor/lib/tool.sh", "e" * 40, "blob"),
        TreeEntry("tests/fixtures/x.sh", "f" * 40, "blob"),
        TreeEntry("link.sh", "0" * 40, "symlink"),
    )
    blobs = {
        "a" * 40: b"#!/bin/sh\necho hi\n",
        "b" * 40: b"#!/usr/bin/env bash\nmake all\n",
        "c" * 40: b"# readme\n",
        "d" * 40: b"all:\n\tcp a b\n",
        "e" * 40: b"echo vendored\n",
        "f" * 40: b"echo fixture\n",
    }
    selected = commands.select(entries)
    assert {entry.path for entry in selected} == {
        "scripts/run.sh",
        "script-no-ext",
        "Makefile",
    }
    files, inputs, issues = commands.repository_files(selected, blobs)
    assert issues == []
    assert set(inputs) == {"scripts/run.sh", "script-no-ext", "Makefile"}
    kinds = {item.path: item.kind for item in files}
    assert kinds == {
        "scripts/run.sh": commands.KIND_SHELL,
        "script-no-ext": commands.KIND_SHELL,
        "Makefile": commands.KIND_MAKEFILE,
    }


def test_shebang_detection() -> None:
    assert commands._has_shell_shebang("#!/bin/sh\necho\n")
    assert commands._has_shell_shebang("#!/usr/bin/env bash\n")
    assert commands._has_shell_shebang("#!/bin/dash -e\n")
    assert commands._has_shell_shebang("#!/bin/ash\n")
    assert not commands._has_shell_shebang("#!/usr/bin/env python3\n")
    assert not commands._has_shell_shebang("#!/bin/fish\n")
    assert not commands._has_shell_shebang("plain text\n")


def test_workflow_yaml_run_extraction() -> None:
    text = (
        "jobs:\n"
        "  a:\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - run: echo one\n"
        "      - run: |\n"
        "          echo two\n"
        "          make three\n"
        "      - run: >-\n"
        "          echo four\n"
        "  b:\n"
        "    runs-on: ubuntu-latest\n"
    )
    runs = commands.fragments(commands.KIND_WORKFLOW, ".github/workflows/x.yml", text)
    assert runs == ("echo one", "echo two\nmake three\n", "echo four")


def test_dockerfile_skips_exec_form_and_flags() -> None:
    text = (
        "FROM alpine\n"
        "RUN apk add make\n"
        "RUN [\"echo\", \"hi\"]\n"
        "RUN --mount=type=cache,target=/c \\\n"
        "    make -j2\n"
    )
    runs = commands.fragments(commands.KIND_DOCKERFILE, "Dockerfile", text)
    assert runs == ("apk add make", "make -j2")


def test_policy_loads_baseline_and_pinned_version() -> None:
    policy = commands.policy()
    assert policy.ast_grep_version == "0.51.3"
    assert {"rm", "cp", "sed", "awk", "grep", "find", "sh", "bash", "xargs"} <= policy.baseline
    assert "git" not in policy.baseline
    assert "make" not in policy.baseline


def _command_graph(root: Path):
    from repomod.dependencies import graph as graph_module

    inventory = write_inventory(
        root,
        [
            repository(
                "acme/one",
                (
                    instance(Ecosystem.COMMAND, "curl", None, context="shell"),
                    instance(Ecosystem.COMMAND, "rm", None, context="makefile"),
                    instance(Ecosystem.COMMAND, "git", None, context="shell"),
                    instance(Ecosystem.COMMAND, "jq", None, context="shell"),
                ),
            ),
            repository(
                "acme/two",
                (
                    instance(Ecosystem.COMMAND, "curl", None, context="workflow"),
                    instance(Ecosystem.COMMAND, "curl", None, context="shell"),
                ),
            ),
        ],
    )
    return graph_module.build_graph(graph_module.load_inventory(inventory))


def _dict(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def test_ownership_commands_section(tmp_path: Path) -> None:
    graph = _command_graph(tmp_path)
    value = ownership.ownership(graph)
    commands_section = _dict(value["commands"])
    totals = _dict(commands_section["totals"])
    assert totals["baseline"] == 1
    assert totals["substitutable"] == 1
    assert totals["external"] == 1
    assert totals["owned"] == 1
    names = _dict(commands_section["names"])
    curl = _dict(names["curl"])
    assert curl["class"] == "external"
    assert curl["repository_count"] == 2
    assert _dict(curl["repositories"])["acme/two"] == {
        "instances": 2,
        "kinds": ["shell", "workflow"],
    }
    git = _dict(names["git"])
    assert git["class"] == "owned"
    assert git["producer"] == "laputa-systems/git-build"
    jq = _dict(names["jq"])
    assert jq["class"] == "substitutable"
    assert jq["producer"] == "laputa-systems/jaq"
    rm = _dict(names["rm"])
    assert rm["class"] == "baseline"
    external_top = commands_section["external_top"]
    assert external_top == [{"name": "curl", "repositories": 2}]
    repositories = _dict(commands_section["repositories"])
    assert _dict(repositories["acme/two"])["external"] == 2
    assert _dict(repositories["acme/one"])["baseline"] == 1
    assert _dict(repositories["acme/one"])["owned"] == 1
    assert _dict(repositories["acme/one"])["substitutable"] == 1
    totals_main = _dict(value["totals"])
    assert totals_main["owned"] == 0
    assert totals_main["upstream"] == 0
    excluded = _dict(value["excluded"])
    assert excluded["command"] == {"components": 4, "instances": 6}


def test_ownership_commands_text_table(tmp_path: Path) -> None:
    graph = _command_graph(tmp_path)
    value = ownership.ownership(graph)
    text = "\n".join(ownership.ownership_text(value))
    assert "commands (unique command names / instances)" in text
    assert "external" in text
    assert "curl (2 repositories)" in text


@pytest.mark.skipif(AST_GREP is None, reason="REPOMOD_AST_GREP is not set")
def test_real_ast_grep_integration() -> None:
    files = [
        commands.SurfaceFile(
            "deploy.sh",
            commands.KIND_SHELL,
            "deploy() {\n  rsync -a src/ dst/\n}\n"
            "cat <<EOF\nignored text\nEOF\n"
            "make release | tee build.log\n",
        )
    ]
    _components, instances, _arguments = commands.extract(files)
    names = {item.purl.rsplit("/", 1)[-1] for item in instances}
    assert names == {"rsync", "cat", "make", "tee"}
