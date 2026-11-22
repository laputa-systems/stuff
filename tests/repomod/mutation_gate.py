from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import io
import json
import os
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCOPES = {
    "removal": ("repomod/clean.py", "x__checkout_removal_blocker", "test_removal_safety.py",
                "first_checkout_blocker or removal_preserves_repository_state"),
    "upstream": ("repomod/sync.py", "x__sync_upstream", "test_sync_upstream.py", ""),
    "matrix": ("repomod/workflow_checks.py", "x__matrix_combinations", "test_github_policy.py", ""),
    "snapshot-entries": ("repomod/dependencies/snapshot.py", "x__entries", "test_deps_snapshot.py", ""),
    "fix-publish": ("repomod/fix.py", "x_push_fix_branch", "test_fix_push.py", ""),
}
GATE_FILE = "tests/repomod/mutation_gate.py"
SETTINGS = frozenset({"Makefile", "pyproject.toml", "uv.lock", ".gitignore", ".python-version", "deploy/uv-version"})
NATIVE_TREES = ("crates/", "docker/", "deploy/", "tests/mycrates/", "tests/worker/", "assets/")
PROVEN_EQUIVALENT = {
    "4b1dce75ca3128ffb800bd608614e474d20de5d8e7d09d754dc022f569a93b0a": {
        "x__matrix_combinations__mutmut_26": "397beb1f359de5229864d726379cd009fb423993f0832e39ecfe8a9208bcf1f9",
        "x__matrix_combinations__mutmut_29": "ae0e1ac1672a1b73dd80f9dcc3e6cd80328f0e05181d120b7f1681eafda0069b",
        "x__matrix_combinations__mutmut_30": "b01e4697b056d31781e6d83e47e6602f21b11d8dc492714e45cb7a37f4711cda",
    },
    "61df99d543e54afaec5177646c8a1b0f638abf42aed3ee3faec412ae2446264a": {
        "x_push_fix_branch__mutmut_29": "47739a2d1fb0f9fd613cbb541221abf33d89b85c6c9a1ae93a1f28a353b1920d",
        "x_push_fix_branch__mutmut_30": "75fa4ca656b92350770b8c8bbcba3f960c1a2d8e89913e7960753bdb3511548f",
        "x_push_fix_branch__mutmut_46": "feed092eaa912a2e1e14cbd9243ddca45f7d843bb6f1ed5a67ea28ad8cde82df",
        "x_push_fix_branch__mutmut_55": "7f208e6afcc6ea5d2eb706fe6bd5b9266126a08fd4b4463c14b4006589b85a1c",
        "x_push_fix_branch__mutmut_67": "f3d77fcb7da8f8d9bc713d240a670a5cd0bd8077503807244eac78fef73c84a9",
        "x_push_fix_branch__mutmut_111": "815b04338021dde4c043e2d6496b291332bc776041af5360d35002b820347262",
    },
}


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def classify(path: str, status: str) -> str:
    if path in SETTINGS or path.startswith((".github/", "fleet/")):
        return "configuration"
    if path.endswith(".md") or path == "LICENSE":
        return "documentation"
    if path.startswith("tests/repomod/"):
        return "configuration" if path == GATE_FILE else "test"
    if path.startswith("repomod/") and path.endswith(".py"):
        return "deleted source" if status == "D" else "source"
    if path.startswith(NATIVE_TREES) or path in {"Cargo.lock", "Cargo.toml", "rust-toolchain.toml"}:
        return "outside repomod"
    raise ValueError(f"unclassified path: {path}")


def outside_function(source: bytes, name: str) -> tuple[list[bytes], list[bytes]] | None:
    functions = [
        node for node in ast.parse(source).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    ]
    if len(functions) != 1:
        return None
    function = functions[0]
    lines = source.splitlines(keepends=True)
    return lines[:function.lineno - 1], lines[function.end_lineno:]


def select(base: str, revision: str) -> dict[str, bool]:
    common = git("merge-base", "--", base, revision).decode("ascii").strip()
    fields = git("diff", "--name-status", "--no-renames", "-z", common, revision, "--").decode().split("\0")
    if fields[-1] != "" or len(fields) % 2 == 0:
        raise ValueError("malformed git diff")
    selected = {}
    sources = {setting[0]: name for name, setting in SCOPES.items()}
    for status, path in zip(fields[0:-1:2], fields[1:-1:2], strict=True):
        if status not in {"A", "M", "D"} or not path:
            raise ValueError(f"unhandled git status: {status} {path}")
        kind = classify(path, status)
        print(f"{kind}: {path}", flush=True)
        if kind in {"configuration", "test", "deleted source"}:
            for shard in SCOPES:
                selected.setdefault(shard, False)
        if kind == "source":
            if path not in sources:
                raise ValueError(f"missing whole-file mutation witness: {path}")
            shard = sources[path]
            whole_file = True
            if status == "M":
                function = SCOPES[shard][1].removeprefix("x_")
                before = outside_function(git("show", f"{common}:{path}"), function)
                after = outside_function(git("show", f"{revision}:{path}"), function)
                whole_file = before is None or before != after
            selected[shard] = whole_file
    return selected


def run_mutmut(directory: Path, selector: str, deadline: float, children: int) -> None:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ValueError("mutation budget exhausted")
    env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    env.pop("PYTHONPATH", None)
    env.pop("MUTANT_UNDER_TEST", None)
    command = [sys.executable, "-m", "mutmut", "run", "--max-children", str(children), selector]

    def cancel(signum: int, _frame: object) -> None:
        raise ValueError(f"mutation run interrupted by signal {signum}")

    previous = {
        sig: signal.signal(sig, cancel) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT)
    }
    try:
        with subprocess.Popen(command, cwd=directory, env=env, start_new_session=True) as process:
            try:
                if code := process.wait(timeout=remaining):
                    raise ValueError(f"mutmut exited {code}: {selector}")
            except subprocess.TimeoutExpired as error:
                raise ValueError("mutation budget exhausted") from error
            finally:
                if process.poll() is None:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def report(directory: Path, source: str, function: str, module: str, whole_file: bool) -> bool:
    mutated = directory / "mutants" / source
    spans_file = mutated.with_suffix(".py.spans")
    spans = json.loads(spans_file.read_text(encoding="utf-8"))
    if spans["version"] != 1:
        raise ValueError(f"unsupported spans: {spans_file}")
    wanted = {
        key: value for key, value in spans["spans"].items()
        if "__mutmut_" in key and not key.endswith("__mutmut_orig")
        and (whole_file or key.startswith(f"{function}__mutmut_"))
    }
    if not wanted:
        raise ValueError(f"empty mutation inventory: {module} {function}")
    meta = json.loads(mutated.with_suffix(".py.meta").read_text(encoding="utf-8"))["exit_code_by_key"]
    lines = mutated.read_bytes().splitlines(keepends=True)
    source_hash = hashlib.sha256((directory / source).read_bytes()).hexdigest()
    passed = True
    for name, (start, end) in sorted(wanted.items()):
        identifier = f"{module}.{name}"
        state = meta.get(identifier)
        if type(state) is int and state == 1:
            result = "caught"
        elif (
            type(state) is int and state == 0
            and PROVEN_EQUIVALENT.get(source_hash, {}).get(name)
            == hashlib.sha256(b"".join(lines[start - 1:end])).hexdigest()
        ):
            result = "equivalent"
        else:
            result = f"unqualified outcome {state!r}"
            passed = False
        print(f"{identifier}: {result}", flush=True)
    print(f"inventory: {len(wanted)}; source sha256: {source_hash}", flush=True)
    return passed


def run_shard(shard: str, whole_file: bool, revision: str, deadline: float) -> bool:
    source, function, test_file, names = SCOPES[shard]
    module = Path(source).with_suffix("").as_posix().replace("/", ".")
    selector = f"{module}.*" if whole_file else f"{module}.{function}__mutmut_*"
    scratch = ROOT / ".work" / "tmp"
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"repomod-mutation-{shard}-", dir=scratch) as tmp:
        directory = Path(tmp)
        raw = git("archive", revision, "repomod", "tests/repomod", "fleet", "pyproject.toml", "uv.lock")
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            entries = archive.getmembers()
            if any(not (entry.isdir() or entry.isfile()) for entry in entries):
                raise ValueError("mutation snapshot contains a link or special file")
            archive.extractall(directory, members=entries, filter="data")
        config = directory / "pyproject.toml"
        test_args = ["-p", "no:parallel"]
        if names:
            test_args.extend(("-k", names))
        with config.open("a", encoding="utf-8") as stream:
            stream.write(
                '\n[tool.mutmut]\nsource_paths = ["repomod"]\nalso_copy = ["fleet"]\n'
                f"only_mutate = {json.dumps([source])}\n"
                f"pytest_add_cli_args = {json.dumps(test_args)}\n"
                f"pytest_add_cli_args_test_selection = {json.dumps([f'tests/repomod/{test_file}'])}\n"
            )
        run_mutmut(directory, selector, deadline, 2 if shard == "fix-publish" else 1)
        return report(directory, source, function, module, whole_file)


def main() -> None:
    parser = argparse.ArgumentParser(description="Trial the serial Repomod mutation selection")
    parser.add_argument("base")
    parser.add_argument("--shard", choices=sorted(SCOPES))
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    if git("status", "--porcelain", "--untracked-files=normal"):
        raise ValueError("commit the selected changes before running the mutation trial")
    revision = git("rev-parse", "HEAD").decode("ascii").strip()
    selected = select(args.base, revision)
    if not selected:
        print("no relevant changes")
        return
    print(json.dumps({name: "whole file" if whole else "protected function" for name, whole in selected.items()}))
    if args.plan:
        return
    if args.shard:
        if args.shard not in selected:
            print(f"no selection for shard {args.shard}")
            return
        selected = {args.shard: selected[args.shard]}
    if version("mutmut") != "3.8.1":
        raise ValueError("mutmut 3.8.1 is required")
    deadline = time.monotonic() + 600
    passed = True
    for shard, whole_file in selected.items():
        passed = run_shard(shard, whole_file, revision, deadline) and passed
    if not passed:
        raise ValueError("mutation trial found a surviving or incomplete identity")


if __name__ == "__main__":
    try:
        main()
    except PackageNotFoundError:
        sys.exit("mutmut 3.8.1 is required")
    except (KeyError, OSError, ValueError, subprocess.SubprocessError, tarfile.TarError) as error:
        sys.exit(str(error))
