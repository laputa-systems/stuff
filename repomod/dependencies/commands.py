from __future__ import annotations

import bisect
import json
import os
import re
import shlex
import shutil
import subprocess
import tomllib
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from ruamel.yaml.scalarstring import FoldedScalarString, LiteralScalarString

from repomod import owned_tools, paths
from repomod.dependencies.git_tree import TreeEntry
from repomod.dependencies.model import (
    Component,
    CoverageKind,
    Ecosystem,
    Instance,
    Issue,
    SourceKind,
    purl,
)

KIND_WORKFLOW = "workflow"
KIND_MAKEFILE = "makefile"
KIND_SHELL = "shell"
KIND_DOCKERFILE = "dockerfile"
SURFACE_KINDS = (KIND_WORKFLOW, KIND_MAKEFILE, KIND_SHELL, KIND_DOCKERFILE)

_AST_GREP_RULES = "id: cmd\nlanguage: bash\nrule:\n  kind: command_name"
_SKIP_DIRECTORIES = frozenset({"fixtures", "testdata", "vendor", "third_party", "node_modules"})
_MAKEFILE_NAMES = frozenset({"Makefile", "makefile", "GNUmakefile"})
_SHELL_SUFFIXES = (".sh", ".bash")
_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.+-]*\Z")
_MAKE_PREFIX = re.compile(r"^[@+\-]+")
_MAKE_VARIABLE = re.compile(r"\$(?:\((?:MAKE|MAKEFLAGS)\)|\{(?:MAKE|MAKEFLAGS)\}|MAKE\b)")
_MAKE_EXPANSION = re.compile(r"\$\([^()\n]*\)|\$\{[^{}\n]*\}")
_FUNCTION_DEF = re.compile(
    r"^\s*(?:function\s+)?([A-Za-z_][A-Za-z0-9_]*)[ \t]*\([ \t]*\)[ \t]*(?:\{|$)",
    re.MULTILINE,
)
_FUNCTION_KEYWORD = re.compile(r"^\s*function[ \t]+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
_SHEBANG = re.compile(r"^#![^\n]*\b(?:ba|da|a)?sh\b")
_RUN_FLAGS = re.compile(r"^--\S+")

_BUILTINS = frozenset(
    {
        "!",
        "(",
        ")",
        ".",
        ":",
        "[",
        "[[",
        "]]",
        "{",
        "}",
        "alias",
        "bg",
        "bind",
        "break",
        "builtin",
        "caller",
        "case",
        "cd",
        "command",
        "compgen",
        "complete",
        "compopt",
        "continue",
        "coproc",
        "declare",
        "dirs",
        "disown",
        "do",
        "done",
        "elif",
        "else",
        "enable",
        "esac",
        "eval",
        "exec",
        "exit",
        "export",
        "fc",
        "fi",
        "fg",
        "for",
        "function",
        "getopts",
        "hash",
        "help",
        "history",
        "if",
        "in",
        "jobs",
        "let",
        "local",
        "logout",
        "mapfile",
        "popd",
        "pushd",
        "pwd",
        "read",
        "readonly",
        "return",
        "select",
        "set",
        "shift",
        "shopt",
        "source",
        "suspend",
        "then",
        "time",
        "times",
        "trap",
        "type",
        "typeset",
        "ulimit",
        "umask",
        "unalias",
        "unset",
        "until",
        "wait",
        "while",
    }
)


class CommandToolError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CommandPolicy:
    ast_grep_version: str
    baseline: frozenset[str]


@dataclass(frozen=True, slots=True)
class SurfaceFile:
    path: str
    kind: str
    text: str


@dataclass(frozen=True, slots=True)
class RawMatch:
    text: str
    offset: int
    line: str = ""
    column: int = 0


@dataclass(frozen=True, slots=True)
class Assembly:
    data: bytes
    spans: tuple[tuple[str, str, int, int], ...]
    marks: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True, slots=True)
class _LocatedFragment:
    text: str
    line: int


@dataclass(frozen=True, slots=True)
class CallSite:
    path: str
    kind: str
    line: int
    name: str
    arguments: tuple[str, ...]


def policy() -> CommandPolicy:
    target = paths.POLICY / "command-baseline.toml"
    try:
        document = tomllib.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"cannot load command baseline policy: {error}") from error
    version = document.get("ast_grep_version")
    commands = document.get("commands")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("command-baseline.toml needs a non-empty ast_grep_version")
    if (
        not isinstance(commands, list)
        or not commands
        or any(not isinstance(item, str) or not item.strip() for item in commands)
    ):
        raise ValueError("command-baseline.toml commands must be a non-empty list of strings")
    return CommandPolicy(version.strip(), frozenset(item.strip() for item in commands))


def baseline_commands() -> frozenset[str]:
    return policy().baseline


def owned_commands() -> dict[str, str]:
    names: dict[str, str] = {}
    producers = sorted(
        owned_tools.load_owned_tools().producers, key=lambda item: str(item.repo).casefold()
    )
    for producer in producers:
        for command in producer.commands:
            names.setdefault(command.name, str(producer.repo))
    return names


def ast_grep_binary() -> Path:
    override = os.environ.get("REPOMOD_AST_GREP")
    if override is not None and len(override) > 0:
        candidate = Path(override).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
        raise CommandToolError(f"REPOMOD_AST_GREP is not an executable file: {override}")
    found = shutil.which("ast-grep")
    if found is None:
        raise CommandToolError(
            "ast-grep is required to inventory shell commands; set REPOMOD_AST_GREP "
            "or install the pinned build on PATH"
        )
    return Path(found)


def ast_grep_version(binary: Path) -> str:
    try:
        result = subprocess.run(
            [str(binary), "--version"], capture_output=True, text=True, timeout=30
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise CommandToolError(f"cannot run ast-grep --version: {error}") from error
    match = re.search(r"ast-grep\s+(\S+)", result.stdout)
    if result.returncode != 0 or match is None:
        raise CommandToolError(
            f"ast-grep --version failed or is unrecognized: {result.stdout.strip()!r}"
        )
    return cast(str, match.group(1))


def require_ast_grep() -> Path:
    binary = ast_grep_binary()
    expected = policy().ast_grep_version
    actual = ast_grep_version(binary)
    if actual != expected:
        raise CommandToolError(
            f"ast-grep {actual} does not match the pinned version {expected} "
            "in fleet/policy/command-baseline.toml"
        )
    return binary


def select(entries: Sequence[TreeEntry]) -> tuple[TreeEntry, ...]:
    return tuple(
        entry
        for entry in entries
        if entry.kind == "blob" and _candidate_path(entry.path)
    )


def repository_files(
    entries: Sequence[TreeEntry], blobs: Mapping[str, bytes]
) -> tuple[list[SurfaceFile], list[str], list[Issue]]:
    files: list[SurfaceFile] = []
    inputs: list[str] = []
    issues: list[Issue] = []
    for entry in select(entries):
        kind = _surface_kind(entry.path)
        data = blobs.get(entry.object_id)
        if data is None:
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            if kind is not None:
                inputs.append(entry.path)
                issues.append(
                    Issue(
                        CoverageKind.NON_UTF8,
                        "dependency input is not UTF-8",
                        path=entry.path,
                    )
                )
            continue
        if kind is None:
            if not _extensionless(entry.path) or not _has_shell_shebang(text):
                continue
            kind = KIND_SHELL
        inputs.append(entry.path)
        files.append(SurfaceFile(entry.path, kind, text))
    return files, inputs, issues


def fragments(kind: str, path: str, text: str) -> tuple[str, ...]:
    return tuple(item.text for item in _located_fragments(kind, path, text))


def _located_fragments(kind: str, path: str, text: str) -> tuple[_LocatedFragment, ...]:
    if kind == KIND_SHELL:
        return (_LocatedFragment(text, 1),) if text.strip() else ()
    if kind == KIND_WORKFLOW:
        return _workflow_fragments(text)
    if kind == KIND_MAKEFILE:
        return _recipe_fragments(text)
    if kind == KIND_DOCKERFILE:
        return _dockerfile_fragments(text)
    return ()


def assemble(files: Sequence[SurfaceFile]) -> Assembly:
    spans: list[tuple[str, str, int, int]] = []
    marks: list[tuple[int, int]] = []
    parts: list[bytes] = []
    offset = 0
    for item in sorted(files, key=lambda file: file.path):
        located = _located_fragments(item.kind, item.path, item.text)
        encoded = [fragment.text.encode("utf-8") for fragment in located]
        body = b"\n".join(encoded)
        if not body.strip():
            continue
        if not body.endswith(b"\n"):
            body += b"\n"
        body += b"\n"
        cursor = offset
        for fragment, chunk in zip(located, encoded, strict=True):
            marks.append((cursor, fragment.line))
            cursor += len(chunk) + 1
        spans.append((item.path, item.kind, offset, offset + len(body)))
        parts.append(body)
        offset += len(body)
    return Assembly(b"".join(parts), tuple(spans), tuple(marks))


def matches_from_json(data: bytes | str) -> tuple[RawMatch, ...]:
    try:
        document = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f"ast-grep returned invalid JSON: {error}") from error
    if not isinstance(document, list):
        raise ValueError("ast-grep returned a non-list JSON document")
    matches: list[RawMatch] = []
    for item in document:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        region = item.get("range")
        offsets = region.get("byteOffset") if isinstance(region, dict) else None
        start = offsets.get("start") if isinstance(offsets, dict) else None
        position = region.get("start") if isinstance(region, dict) else None
        column = position.get("column") if isinstance(position, dict) else None
        source = item.get("lines")
        if not isinstance(text, str) or type(start) is not int:
            continue
        matches.append(
            RawMatch(
                text,
                start,
                source if isinstance(source, str) else "",
                column if type(column) is int else 0,
            )
        )
    return tuple(matches)


def scan(data: bytes, binary: Path | None = None) -> tuple[RawMatch, ...]:
    tool = binary if binary is not None else require_ast_grep()
    try:
        result = subprocess.run(
            [
                str(tool),
                "scan",
                "--inline-rules",
                _AST_GREP_RULES,
                "--json=compact",
                "--stdin",
            ],
            input=data,
            capture_output=True,
            timeout=300,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise CommandToolError(f"cannot run ast-grep scan: {error}") from error
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise CommandToolError(f"ast-grep scan failed: {detail or f'exit {result.returncode}'}")
    return matches_from_json(result.stdout)


def _span_at(
    assembly: Assembly, offset: int
) -> tuple[str, str, int, int] | None:
    starts = [span[2] for span in assembly.spans]
    index = bisect.bisect_right(starts, offset) - 1
    if index < 0:
        return None
    path, kind, start, end = assembly.spans[index]
    if not start <= offset < end:
        return None
    return path, kind, start, end


def file_commands(
    assembly: Assembly, matches: Sequence[RawMatch]
) -> dict[str, tuple[str, Counter[str], dict[str, set[str]]]]:
    functions = {
        span[0]: _defined_functions(assembly, span) for span in assembly.spans
    }
    found: dict[str, tuple[str, Counter[str], dict[str, set[str]]]] = {}
    for match in matches:
        located = _span_at(assembly, match.offset)
        if located is None:
            continue
        path, kind, _start, _end = located
        name = _normalize(match.text)
        if name is None or name in _BUILTINS or name in functions[path]:
            continue
        entry = found.get(path)
        if entry is None:
            entry = (kind, Counter(), defaultdict(set))
            found[path] = entry
        assert entry[0] == kind
        entry[1][name] += 1
        arguments = _arguments(match)
        if arguments:
            entry[2].setdefault(name, set()).add(arguments)
    return found


def sites(assembly: Assembly, matches: Sequence[RawMatch]) -> tuple[CallSite, ...]:
    functions = {
        span[0]: _defined_functions(assembly, span) for span in assembly.spans
    }
    mark_offsets = [mark[0] for mark in assembly.marks]
    found: list[CallSite] = []
    for match in matches:
        located = _span_at(assembly, match.offset)
        if located is None:
            continue
        path, kind, _start, _end = located
        name = _normalize(match.text)
        if name is None or name in _BUILTINS or name in functions[path]:
            continue
        found.append(
            CallSite(
                path,
                kind,
                _source_line(assembly, mark_offsets, match.offset),
                name,
                _argument_words(_arguments(match)),
            )
        )
    return tuple(found)


def call_sites(files: Sequence[SurfaceFile]) -> tuple[CallSite, ...]:
    assembly = assemble(files)
    if not assembly.data.strip():
        return ()
    return sites(assembly, scan(assembly.data))


def _source_line(
    assembly: Assembly, mark_offsets: Sequence[int], offset: int
) -> int:
    index = bisect.bisect_right(mark_offsets, offset) - 1
    if index < 0:
        return 1
    mark_offset, first_line = assembly.marks[index]
    return first_line + assembly.data[mark_offset:offset].count(b"\n")


_CONTROL_OPERATORS = frozenset({"&&", "||", ";", "|", "&"})


def _argument_words(text: str) -> tuple[str, ...]:
    if not text:
        return ()
    try:
        words = shlex.split(text, posix=True)
    except ValueError:
        words = text.split()
    for index, word in enumerate(words):
        if word in _CONTROL_OPERATORS:
            return tuple(words[:index])
    return tuple(words)


def _arguments(match: RawMatch) -> str:
    line = match.line
    if not line:
        return ""
    column = match.column
    end = column + len(match.text)
    if column >= 0 and end <= len(line) and line[column:end] == match.text:
        return line[end:].strip()
    index = line.find(match.text)
    if index < 0:
        return ""
    return line[index + len(match.text) :].strip()


def extract(
    files: Sequence[SurfaceFile],
) -> tuple[tuple[Component, ...], tuple[Instance, ...], dict[str, tuple[str, ...]]]:
    assembly = assemble(files)
    if not assembly.data.strip():
        return (), (), {}
    return inventory(assembly, scan(assembly.data))


def inventory(
    assembly: Assembly, matches: Sequence[RawMatch]
) -> tuple[tuple[Component, ...], tuple[Instance, ...], dict[str, tuple[str, ...]]]:
    found = file_commands(assembly, matches)
    kinds_by_name: dict[str, set[str]] = defaultdict(set)
    arguments: dict[str, set[str]] = defaultdict(set)
    for kind, counts, args_by_name in found.values():
        for name in counts:
            kinds_by_name[name].add(kind)
            instance_id = f"{purl(Ecosystem.COMMAND, name)}#{kind}"
            arguments[instance_id].update(args_by_name.get(name, ()))
    components = tuple(
        Component(
            purl(Ecosystem.COMMAND, name),
            Ecosystem.COMMAND,
            name,
            name,
        )
        for name in sorted(kinds_by_name)
    )
    instances = tuple(
        Instance(
            id=f"{purl(Ecosystem.COMMAND, name)}#{kind}",
            purl=purl(Ecosystem.COMMAND, name),
            component=purl(Ecosystem.COMMAND, name),
            version=None,
            source_kind=SourceKind.PATH,
            context=kind,
        )
        for name in sorted(kinds_by_name)
        for kind in sorted(kinds_by_name[name])
    )
    return (
        components,
        instances,
        {
            instance_id: tuple(sorted(arguments.get(instance_id, ())))
            for instance_id in (
                f"{purl(Ecosystem.COMMAND, name)}#{kind}"
                for name in sorted(kinds_by_name)
                for kind in sorted(kinds_by_name[name])
            )
        },
    )


def candidate_path(path: str) -> bool:
    return _candidate_path(path)


def surface_file(path: str, text: str) -> SurfaceFile | None:
    if not _candidate_path(path):
        return None
    kind = _surface_kind(path)
    if kind is None:
        if not _extensionless(path) or not _has_shell_shebang(text):
            return None
        kind = KIND_SHELL
    return SurfaceFile(path, kind, text)


def _candidate_path(path: str) -> bool:
    parts = path.split("/")[:-1]
    if any(part in _SKIP_DIRECTORIES for part in parts):
        return False
    return _surface_kind(path) is not None or _extensionless(path)


def _surface_kind(path: str) -> str | None:
    workflow = path.removeprefix(".github/workflows/")
    if (
        path.startswith(".github/workflows/")
        and "/" not in workflow
        and workflow.endswith((".yml", ".yaml"))
    ):
        return KIND_WORKFLOW
    name = path.rsplit("/", 1)[-1]
    if name in _MAKEFILE_NAMES or name.endswith(".mk"):
        return KIND_MAKEFILE
    if _dockerfile_name(name):
        return KIND_DOCKERFILE
    if name.endswith(_SHELL_SUFFIXES):
        return KIND_SHELL
    return None


def _dockerfile_name(name: str) -> bool:
    for base in ("Dockerfile", "Containerfile"):
        if name == base or name.startswith(f"{base}.") or name.endswith(f".{base}"):
            return True
    return False


def _extensionless(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return bool(name) and "." not in name


def _has_shell_shebang(text: str) -> bool:
    first = text.split("\n", 1)[0]
    return _SHEBANG.match(first) is not None


def _workflow_line(node: object, key: object, value: object) -> int:
    data = getattr(getattr(node, "lc", None), "data", None)
    entry = data.get(key) if isinstance(data, dict) else None
    if not (
        isinstance(entry, list)
        and len(entry) >= 4
        and all(type(item) is int for item in entry[:4])
    ):
        return 1
    key_line = int(entry[0])
    _key_column = entry[1]
    value_line = int(entry[2])
    _value_column = entry[3]
    if isinstance(value, (LiteralScalarString, FoldedScalarString)):
        return key_line + 2
    if value_line > key_line:
        return value_line + 1
    return key_line + 1


def _workflow_fragments(text: str) -> tuple[_LocatedFragment, ...]:
    if not text.strip():
        return ()
    try:
        document = YAML(typ="rt").load(text)
    except (YAMLError, AttributeError, ValueError, RecursionError):
        return ()
    runs: list[_LocatedFragment] = []

    def walk(node: object) -> None:
        if isinstance(node, Mapping):
            for key, value in node.items():
                if key == "run" and isinstance(value, str):
                    runs.append(_LocatedFragment(value, _workflow_line(node, key, value)))
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(document)
    return tuple(runs)


def _recipe_fragments(text: str) -> tuple[_LocatedFragment, ...]:
    recipes: list[_LocatedFragment] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line.startswith("\t"):
            continue
        start = index
        command = line[1:]
        while command.rstrip().endswith("\\") and index < len(lines):
            command = command.rstrip()[:-1] + " " + lines[index].strip()
            index += 1
        command = _MAKE_PREFIX.sub("", command).strip()
        command = _MAKE_VARIABLE.sub("make", command)
        command = _MAKE_EXPANSION.sub("$MAKEVAR", command)
        if command:
            recipes.append(_LocatedFragment(command, start))
    return tuple(recipes)


def _dockerfile_fragments(text: str) -> tuple[_LocatedFragment, ...]:
    runs: list[_LocatedFragment] = []
    for line, start in _logical_lines(text):
        match = re.match(r"^\s*RUN(?:\s|$)", line, re.IGNORECASE)
        if match is None:
            continue
        rest = line[match.end() :].strip()
        if not rest or rest.startswith("["):
            continue
        while True:
            flag = _RUN_FLAGS.match(rest)
            if flag is None:
                break
            rest = rest[flag.end() :].lstrip()
        if rest:
            runs.append(_LocatedFragment(rest, start))
    return tuple(runs)


def _logical_lines(text: str) -> list[tuple[str, int]]:
    lines: list[tuple[str, int]] = []
    pending = ""
    pending_line = 0
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip("\n")
        if line.endswith("\\"):
            if not pending:
                pending_line = number
            pending += line[:-1] + " "
            continue
        lines.append((pending + line, pending_line or number))
        pending = ""
        pending_line = 0
    if pending:
        lines.append((pending, pending_line))
    return lines


def _defined_functions(assembly: Assembly, span: tuple[str, str, int, int]) -> frozenset[str]:
    _path, _kind, start, end = span
    text = assembly.data[start:end].decode("utf-8", "replace")
    names = {match.group(1) for match in _FUNCTION_DEF.finditer(text)}
    names.update(match.group(1) for match in _FUNCTION_KEYWORD.finditer(text))
    return frozenset(names)


def _normalize(text: str) -> str | None:
    name = text.strip()
    if not name:
        return None
    if "/" in name:
        name = name.rsplit("/", 1)[-1]
    if not _NAME.fullmatch(name):
        return None
    return name
