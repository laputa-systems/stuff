from __future__ import annotations

import fnmatch
import re
import tomllib
from pathlib import Path

from repomod.rules.release import _POLICY
from repomod.rules.workflows import read_workflow_sources
from repomod.types import Finding, Repository, Rule, TagPredicate, operational, violation

_RULE = "release-archive-format"
_PUBLISH = re.compile(
    r"\bgh\s+release\s+(?:create|upload)\b|softprops/action-gh-release|cargo-dist|\bdist\s+(?:plan|build|host)\b",
    re.IGNORECASE,
)
_SCRIPT = re.compile(r"(?:\./)?((?:scripts|tools)/[\w./-]+(?:\.(?:sh|py)|/make-archive))\b")
_MAKE = re.compile(r"\bmake\s+([\w-]+)")
_TAR = re.compile(r"(?<![.\w/-])tar\b[^\n]*?(?:--create\b|(?:^|\s)-?[a-zA-Z]*c[a-zA-Z]*\b)")
_ZIP = re.compile(
    r"(?:(?<![.\w/-])zip\s+|\bditto\s+[^\n]*-c\b[^\n]*-k\b"
    r"|\bzipfile\.ZipFile\s*\([^\n]*[,=]\s*['\"](?:w|x|a)['\"]|\b(?:tools/)?make-archive\b)"
)
_PY_TAR = re.compile(r"\btarfile\.open\s*\([^\n]*[,=]\s*['\"]w(?::[^'\"]*)?['\"]")
_PACKAGE_INSTALL = re.compile(r"\b(?:apk\s+add|apt(?:-get)?\s+install|brew\s+install|dnf\s+install)\b")
_ASSET = re.compile(r"[^\s\"'`(),]+\.(?:zip|tar\.gz|tar\.zst|tgz|tar)(?![\w.])", re.IGNORECASE)



def _exempt(repository: Repository, value: str) -> bool:
    return any(
        fnmatch.fnmatchcase(str(repository.id), entry["repository"])
        and fnmatch.fnmatchcase(Path(value).name, entry["pattern"])
        for entry in _POLICY["archive"]["exemptions"]
    )


def _read(root: Path, relative: str) -> str | None:
    path = root / relative
    parts = path.relative_to(root).parts
    if any((root / Path(*parts[:index])).is_symlink() for index in range(1, len(parts) + 1)):
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None


def _findings(root: Path, repository: Repository) -> list[Finding]:
    if repository.private:
        return []
    workflows, problems = read_workflow_sources(root, repository)
    findings = [operational(repository, _RULE, path, message) for path, message in problems]
    release_sources = [(path, source) for path, source in workflows if _PUBLISH.search(source)]
    if not release_sources:
        return findings
    sources = dict(release_sources)
    available_workflows = dict(workflows)
    pending = list(sources.values())
    seen_targets: set[str] = set()
    while pending:
        source = pending.pop()
        for relative in re.findall(r"uses:\s*\./(\.github/workflows/[\w.-]+\.ya?ml)", source):
            if relative not in sources and relative in available_workflows:
                sources[relative] = available_workflows[relative]
                pending.append(available_workflows[relative])
        for match in _SCRIPT.finditer(source):
            relative = match.group(1)
            if ".." in Path(relative).parts or relative in sources:
                continue
            content = _read(root, relative)
            if content is not None:
                sources[relative] = content
                pending.append(content)
        makefile = _read(root, "Makefile")
        if makefile is not None:
            for target in _MAKE.findall(source):
                if target in seen_targets:
                    continue
                seen_targets.add(target)
                lines = makefile.splitlines()
                for index, line in enumerate(lines):
                    if re.match(rf"^{re.escape(target)}\s*:", line):
                        end = index + 1
                        while end < len(lines) and (lines[end].startswith("\t") or not lines[end].strip()):
                            end += 1
                        body = "\n" * index + "\n".join(lines[index:end])
                        sources[f"Makefile:{target}"] = body
                        pending.append(body)
                        break
    for path, source in sources.items():
        actual_path = path.split(":", 1)[0]
        lines = source.splitlines()
        upload = False
        command = False
        continuation = ""
        start = 0
        for number, raw in enumerate(lines, 1):
            if continuation:
                line = continuation + " " + raw.strip()
            else:
                line = raw
                start = number
            if line.rstrip().endswith("\\"):
                continuation = line.rstrip()[:-1]
                continue
            continuation = ""
            number = start
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if re.search(r"-\s+(?:name|uses|run):", line):
                upload = bool(re.search(r"(?:upload-artifact|action-gh-release)", line))
                command = False
            if re.search(r"(?:upload-artifact|action-gh-release)@", line):
                upload = True
            if re.search(r"\bgh\s+release\s+(?:create|upload)\b", line):
                command = True
            asset = _ASSET.search(line)
            construct = None
            tar = _PY_TAR.search(line) or (
                _TAR.search(line)
                and _PACKAGE_INSTALL.search(line) is None
                and (asset or re.search(r"\btar\b[^\n]*\s-?[a-zA-Z]*f[a-zA-Z]*\b|\|\s*gzip\b", line))
            )
            standard_tar = re.search(r"(?:\.tar\.xz|\bcJf\b|\b-cJf\b|\|\s*xz\b|w:xz)", line)
            if _ZIP.search(line) or (tar and not standard_tar) or (asset and (upload or command)):
                construct = stripped
            if construct is not None and not (asset and _exempt(repository, asset.group())):
                findings.append(
                    violation(
                        repository, _RULE, actual_path, f"release archive must be tar.xz: {construct}", line=number
                    )
                )
            if command and not line.rstrip().endswith("\\"):
                command = False
    if any("cargo-dist" in source or "dist plan" in source for _, source in release_sources):
        for path in ("dist-workspace.toml", "dist.toml", "Cargo.toml"):
            source = _read(root, path)
            if source is None:
                continue
            try:
                data = tomllib.loads(source)
            except tomllib.TOMLDecodeError:
                continue
            dist = (
                data.get("dist") if path != "Cargo.toml"
                else data.get("workspace", {}).get("metadata", {}).get("dist")
            )
            if not isinstance(dist, dict):
                continue
            value = dist.get("unix-archive", ".tar.xz")
            if isinstance(value, str) and value != ".tar.xz":
                lines = source.splitlines()
                default_line = next(
                    (i for i, line in enumerate(lines, 1) if line.strip() in {"[dist]", "[workspace.metadata.dist]"}), 1
                )
                number = next((i for i, line in enumerate(lines, 1) if "unix-archive" in line), default_line)
                findings.append(violation(repository, _RULE, path, f"cargo-dist unix-archive is {value}", line=number))
    return findings


def release_archive_rules() -> tuple[Rule, ...]:
    return (Rule(_RULE, "Require tar.xz release archives", TagPredicate(), _findings, None, None, ()),)
