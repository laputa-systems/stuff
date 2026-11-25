"""Rewrite Dockerfile `apk add` installs onto the owned-tools image.

`rewrite` removes image-covered packages from `apk add` argument lists inside
Alpine stages, drops RUN instructions or `&&`/`;`-chained apk commands that
become empty, and inserts the image `COPY`/`ENV` pair once per touched stage.
Anything the parser cannot rewrite safely is left untouched; `removed` records
which `(line, package)` pairs the rewrite actually dropped so callers can mark
exactly those findings fixable.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from repomod.install_parse import package_name

_IMAGE_PATH = "/opt/laputa"
_INSTRUCTION = re.compile(r"^[ \t]*[A-Za-z]")
_KEYWORD = re.compile(r"^[ \t]*([A-Za-z][A-Za-z0-9_-]*)")
_UNSAFE = re.compile(r"[\"'`$()<>#]")
_LOOSE_SEPARATOR = re.compile(r"(?<!&)&(?!&)|(?<!\|)\|(?!\|)")
_SEGMENT_SPLIT = re.compile(r"([ \t]*(?:&&|\|\||;)[ \t]*)")
_SEPARATOR_OP = re.compile(r"&&|\|\||;")
_COPY_FROM = re.compile(r"^[ \t]*COPY[ \t]+--from=(\S+)", re.IGNORECASE)
_ENV_PATH = re.compile(r"PATH=(?:/opt/laputa/bin:\$PATH|\$PATH:/opt/laputa/bin)(?![\w:/])")
_PREPENDED_PATH = re.compile(r"^([ \t]*ENV[ \t]+PATH=)/opt/laputa/bin:\$PATH([ \t]*)$", re.IGNORECASE)
_ALPINE_NAME = re.compile(r"alpine(?:[.-][0-9][\w.-]*)?", re.IGNORECASE)
_APK_VALUE_FLAGS = frozenset({
    "--virtual", "-t", "--repository", "-X", "--arch", "-a",
    "--cache-dir", "--keys-dir", "--fetch-timeout", "--timeout", "--proxy",
    "--mirror", "--allow-untrusted", "--force-non-repository",
    "--force-overwrite", "--force-old-package", "--latest", "-l",
})
_APK_SAFE_FLAGS = frozenset({
    "--no-cache", "--no-network", "--update-cache", "--clean-protected-names",
    "--simulate", "-s", "--quiet", "-q", "--interactive", "-i",
    "--progress", "--upgrade", "-u", "--available",
})
_APK_PRE_SAFE = frozenset({"-q", "--quiet", "-v", "--verbose"})


@dataclass(frozen=True, slots=True)
class Rewrite:
    text: str
    removed: frozenset[tuple[int, str]]
    prepended: frozenset[int] = frozenset()
    stale: frozenset[int] = frozenset()


@dataclass(frozen=True, slots=True)
class _Block:
    start: int
    end: int
    keyword: str


def _eol(raw: str) -> str:
    if raw.endswith("\r\n"):
        return "\r\n"
    if raw.endswith(("\n", "\r")):
        return raw[-1:]
    return "\n"


def _continued(raw: str) -> bool:
    body = raw.rstrip("\r\n").rstrip()
    return body.endswith("\\") and not body.endswith("\\\\")


def _blocks(lines: list[str]) -> list[_Block]:
    blocks: list[_Block] = []
    index = 0
    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or not _INSTRUCTION.match(raw):
            index += 1
            continue
        keyword = _KEYWORD.match(raw)
        if keyword is None:
            index += 1
            continue
        start = index
        end = index
        while end < len(lines):
            end += 1
            if end >= len(lines) or not _continued(lines[end - 1]):
                break
        blocks.append(_Block(start, end, keyword.group(1).upper()))
        index = end
    return blocks


def _logical(lines: list[str]) -> str:
    parts: list[str] = []
    for index, raw in enumerate(lines):
        body = raw.rstrip("\r\n").rstrip()
        if index < len(lines) - 1:
            body = body[:-1].rstrip()
        parts.append(body)
    return " ".join(" ".join(parts).split())


def _from_image(lines: list[str], block: _Block) -> str | None:
    words = _logical(lines[block.start : block.end]).split()
    if len(words) < 2:
        return None
    for word in words[1:]:
        if word.startswith("--"):
            continue
        return word
    return None


def _is_alpine(image: str | None) -> bool:
    if image is None:
        return False
    name = image.split("@", 1)[0].rsplit("/", 1)[-1].split(":", 1)[0]
    return _ALPINE_NAME.fullmatch(name) is not None


def _entry_match(entry: str, name: str) -> bool:
    if entry.startswith("^"):
        try:
            return re.fullmatch(entry, name) is not None
        except re.error:
            return False
    return entry.casefold() == name.casefold()


def _covered(name: str, packages: tuple[str, ...]) -> bool:
    return any(_entry_match(entry, name) for entry in packages)


def _package_tokens(args: list[str]) -> list[str]:
    tokens: list[str] = []
    index = 0
    while index < len(args):
        token = args[index]
        if token.startswith("-") and token != "-":
            index += 2 if "=" not in token and token in _APK_VALUE_FLAGS else 1
            continue
        tokens.append(token)
        index += 1
    return tokens


def _segment(segment: str, packages: tuple[str, ...], keep: Callable[[str], bool]) -> tuple[str, list[str]] | None:
    words = segment.split()
    if len(words) < 3 or words[0] != "apk":
        return None
    index = 1
    while index < len(words) and words[index].startswith("-"):
        if "=" not in words[index] and words[index] not in _APK_PRE_SAFE:
            return None
        index += 1
    if index >= len(words) or words[index] != "add":
        return None
    pre = words[1:index]
    args = words[index + 1 :]
    kept: list[str] = []
    removed: list[str] = []
    cursor = 0
    while cursor < len(args):
        token = args[cursor]
        if token.startswith("-") and token != "-":
            if "=" in token:
                kept.append(token)
                cursor += 1
                continue
            if token in _APK_VALUE_FLAGS:
                if cursor + 1 >= len(args):
                    return None
                kept.extend((token, args[cursor + 1]))
                cursor += 2
                continue
            if token in _APK_SAFE_FLAGS or token == "--":
                kept.append(token)
                cursor += 1
                continue
            return None
        name = package_name(token)
        if name and _covered(name, packages) and not keep(name):
            removed.append(name)
        else:
            kept.append(token)
        cursor += 1
    if not removed:
        return None
    if not _package_tokens(kept):
        return ("drop", removed)
    return (" ".join(["apk", *pre, "add", *kept]), removed)


def _separator_op(separator: str) -> str:
    match = _SEPARATOR_OP.search(separator)
    return match.group(0) if match else ";"


def _strip_in_place(lines: list[str], names: list[str]) -> list[str] | None:
    wanted = {name.casefold() for name in names}
    output: list[str] = []
    saw_apk = in_add = skip_value = False
    for raw in lines:
        eol = _eol(raw)
        body = raw[: len(raw) - len(eol)]
        stripped = body.rstrip(" \t")
        continued = stripped.endswith("\\")
        content = stripped[:-1] if continued else body
        spans: list[tuple[int, int]] = []
        for match in re.finditer(r"\S+", content):
            token = match.group(0)
            if token in ("&&", "||", ";"):
                saw_apk = in_add = skip_value = False
            elif _SEPARATOR_OP.search(token):
                return None
            elif skip_value:
                skip_value = False
            elif token == "apk" and not in_add:
                saw_apk = True
            elif saw_apk and not in_add and token == "add":
                in_add = True
            elif in_add and token in _APK_VALUE_FLAGS:
                skip_value = True
            elif in_add and not token.startswith("-") and package_name(token).casefold() in wanted:
                before = content[: match.start()]
                if before.strip():
                    spans.append((len(before.rstrip(" \t")), match.end()))
                else:
                    after = len(content) - len(content[match.end():].lstrip(" \t"))
                    spans.append((match.start(), after))
        for start, end in reversed(spans):
            content = content[:start] + content[end:]
        if spans and not content.strip():
            if not continued:
                if not output:
                    return None
                previous = output[-1]
                previous_eol = _eol(previous)
                kept = previous[: len(previous) - len(previous_eol)].rstrip(" \t")
                output[-1] = kept[:-1].rstrip(" \t") + eol
            continue
        if continued:
            output.append(content.rstrip(" \t") + (" \\" if content.strip() else "\\") + eol if spans else raw)
        else:
            output.append(content + eol if spans else raw)
    return output


def _rewrite_run(
    lines: list[str],
    packages: tuple[str, ...],
    keep: Callable[[str], bool],
) -> tuple[list[str], list[str]] | None:
    logical = _logical(lines)
    words = logical.split()
    if len(words) < 2 or words[0].upper() != "RUN":
        return None
    index = 1
    flags: list[str] = []
    while index < len(words) and words[index].startswith("--"):
        flags.append(words[index])
        index += 1
    command = " ".join(words[index:])
    if not command or _UNSAFE.search(command) or _LOOSE_SEPARATOR.search(command):
        return None
    parts = _SEGMENT_SPLIT.split(command)
    segments = parts[0::2]
    separators = parts[1::2]
    rebuilt: list[str | None] = []
    removed: list[str] = []
    dropped: set[int] = set()
    changed = False
    for position, segment in enumerate(segments):
        result = _segment(segment, packages, keep)
        if result is None:
            rebuilt.append(segment.strip())
            continue
        changed = True
        action, names = result
        removed.extend(names)
        if action == "drop":
            dropped.add(position)
            rebuilt.append(None)
        else:
            rebuilt.append(action)
    if not changed or not removed:
        return None
    for position in dropped:
        left = separators[position - 1] if position > 0 else None
        right = separators[position] if position < len(segments) - 1 else None
        if (left is not None and _separator_op(left) == "||") or (
            right is not None and _separator_op(right) == "||"
        ):
            return None
    if not dropped:
        in_place = _strip_in_place(lines, removed)
        if in_place is not None:
            return (in_place, removed)
    kept = [(position, text) for position, text in enumerate(rebuilt) if text is not None]
    if not kept:
        return ([], removed)
    pieces = [kept[0][1]]
    for position, text in kept[1:]:
        separator = separators[position - 1] if position > 0 else ";"
        pieces.append(f" {_separator_op(separator)} {text}")
    command_text = "".join(pieces)
    indent_match = re.match(r"^[ \t]*", lines[0])
    indent = indent_match.group(0) if indent_match is not None else ""
    eol = _eol(lines[0])
    flag_text = f" {' '.join(flags)}" if flags else ""
    return ([f"{indent}{words[0]}{flag_text} {command_text}{eol}"], removed)


def _copy_from_value(lines: list[str], block: _Block) -> str | None:
    match = _COPY_FROM.match(_logical(lines[block.start : block.end]))
    if match is None:
        return None
    value = match.group(1)
    return value if isinstance(value, str) else None


def _stage_has_image_copy(lines: list[str], blocks: list[_Block], start: int, end: int, reference: str) -> bool:
    for block in blocks:
        if block.keyword != "COPY" or block.start < start or block.start >= end:
            continue
        value = _copy_from_value(lines, block)
        if value is not None and (value == reference or value.startswith(reference + "@")):
            return True
    return False


def _update_image_copies(lines: list[str], blocks: list[_Block], image: str) -> set[int]:
    updated_lines: set[int] = set()
    for block in blocks:
        if block.keyword != "COPY":
            continue
        value = _copy_from_value(lines, block)
        reference = image.split("@", 1)[0]
        if value is None or not (value == reference or value.startswith(reference + "@")):
            continue
        if value == image:
            continue
        pattern = re.compile(r"(--from=)" + re.escape(value) + r"(\s|$)")
        updated = pattern.sub(rf"\g<1>{image}\g<2>", lines[block.start], count=1)
        if updated == lines[block.start]:
            continue
        lines[block.start] = updated
        updated_lines.add(block.start + 1)
    return updated_lines


def _stage_has_env_path(lines: list[str], blocks: list[_Block], start: int, end: int) -> bool:
    for block in blocks:
        if block.keyword != "ENV" or block.start < start or block.start >= end:
            continue
        if _ENV_PATH.search(_logical(lines[block.start : block.end])):
            return True
    return False


def rewrite(
    text: str,
    packages: tuple[str, ...],
    image: str,
    keep: Callable[[str], bool],
) -> Rewrite:
    lines = text.splitlines(keepends=True)
    blocks = _blocks(lines)
    froms = [block for block in blocks if block.keyword == "FROM"]
    edits: list[tuple[int, int, list[str]]] = []
    removed: set[tuple[int, str]] = set()
    stale = _update_image_copies(lines, blocks, image)
    for stage, from_block in enumerate(froms):
        stage_end = froms[stage + 1].start if stage + 1 < len(froms) else len(lines)
        if not _is_alpine(_from_image(lines, from_block)):
            continue
        stage_removed: list[str] = []
        for block in blocks:
            if block.keyword != "RUN" or block.start < from_block.end or block.start >= stage_end:
                continue
            result = _rewrite_run(lines[block.start : block.end], packages, keep)
            if result is None:
                continue
            new_lines, names = result
            edits.append((block.start, block.end, new_lines))
            stage_removed.extend(names)
            removed.update((block.start + 1, name.casefold()) for name in names)
        if not stage_removed:
            continue
        reference = image.split("@", 1)[0]
        copy_present = _stage_has_image_copy(lines, blocks, from_block.end, stage_end, reference)
        env_present = _stage_has_env_path(lines, blocks, from_block.end, stage_end)
        insert_at = from_block.end
        eol = _eol(lines[from_block.end - 1]) if from_block.end else "\n"
        inserted: list[str] = []
        if not copy_present:
            inserted.append(f"COPY --from={image} {_IMAGE_PATH} {_IMAGE_PATH}{eol}")
        if not env_present:
            inserted.append(f"ENV PATH=$PATH:/opt/laputa/bin{eol}")
        if inserted:
            edits.append((insert_at, insert_at, inserted))
    prepended: set[int] = set()
    for block in blocks:
        if block.keyword != "ENV" or block.end - block.start != 1:
            continue
        raw = lines[block.start]
        eol = _eol(raw)
        match = _PREPENDED_PATH.match(raw[: len(raw) - len(eol)])
        if match is None:
            continue
        edits.append((block.start, block.end, [f"{match.group(1)}$PATH:/opt/laputa/bin{match.group(2)}{eol}"]))
        prepended.add(block.start + 1)
    if not edits and not stale:
        return Rewrite(text, frozenset())
    output: list[str] = []
    cursor = 0
    for start, end, replacement in sorted(edits):
        output.extend(lines[cursor:start])
        output.extend(replacement)
        cursor = end
    output.extend(lines[cursor:])
    return Rewrite("".join(output), frozenset(removed), frozenset(prepended), frozenset(stale))
