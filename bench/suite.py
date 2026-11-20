from __future__ import annotations

import argparse
import importlib.util
import json
import os
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
TIERS = ("edit", "change", "scenario", "full")
WORKLOADS = {"selection": "edit", "preview-render": "change"}


def select(tier: str, workload: str, allow_full: bool) -> list[str]:
    if tier not in TIERS:
        raise ValueError(f"unknown tier: {tier}")
    if tier == "full" and not allow_full:
        raise ValueError("full tier requires ALLOW_FULL=1")
    if workload and workload not in WORKLOADS:
        raise ValueError(f"unknown workload: {workload}")
    selected = [name for name, level in WORKLOADS.items() if TIERS.index(level) <= TIERS.index(tier)]
    if workload:
        selected = [name for name in selected if name == workload]
    if not selected:
        raise ValueError("empty workload selection")
    return selected


def preflight(selected: list[str]) -> None:
    required = [ROOT / "tests/repomod/test_bench_suite.py"] if "selection" in selected else []
    if "preview-render" in selected:
        required.extend(ROOT / path for path in (
            "tests/repomod/test_dashboard_preview.py", "tests/fixtures/dashboard/golden.json",
            "tests/fixtures/dashboard/meta.json", "tests/fixtures/dashboard/status.json",
            "tests/fixtures/dashboard/enrichment.json", "tests/fixtures/dashboard/inventory/index.json",
            "tests/fixtures/dashboard/loc/index.json",
        ))
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ValueError(f"missing inputs for {', '.join(selected)}: {', '.join(missing)}; restore tracked fixtures")
    if "selection" in selected and importlib.util.find_spec("pytest") is None:
        raise ValueError("selection needs pytest; install the project's dev environment")


def render_preview() -> None:
    from repomod.dependencies import preview

    spec = importlib.util.spec_from_file_location("preview_golden", ROOT / "tests/repomod/test_dashboard_preview.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load preview golden summarizer")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory(prefix="bench-preview-") as directory:
        output = Path(directory) / "dashboard"
        start_wall = time.perf_counter()
        start_cpu = time.process_time()
        preview.render_preview(output)
        wall = time.perf_counter() - start_wall
        cpu = time.process_time() - start_cpu
        actual = module.summarize(output)
        golden = json.loads((preview.FIXTURE / "golden.json").read_text(encoding="utf-8"))
        if actual != golden:
            raise ValueError("preview content differs from golden.json")
        print("preview-render: golden content check passed")
        print(json.dumps({"workload": "preview-render", "wall_seconds": wall, "cpu_seconds": cpu,
                          "peak_rss_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                          "peak_rss_unit": "bytes" if sys.platform == "darwin" else "KiB",
                          "timing_validity": "operability only; no performance verdict"}))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("list", "check", "run"))
    args = parser.parse_args()
    if args.action == "list":
        print("selection\tedit\tharness selection and preflight self-tests\testimated seconds")
        print("preview-render\tchange\tcanonical preview render and golden content\testimated seconds")
        return 0
    try:
        selected = select(os.environ.get("TIER", "edit"), os.environ.get("WORKLOAD", ""),
                          os.environ.get("ALLOW_FULL") == "1")
        preflight(selected)
        for name in selected:
            print(f"selected: {name} ({WORKLOADS[name]})", flush=True)
        if args.action == "check":
            print("preflight passed; dry selection only")
        else:
            for name in selected:
                if name == "selection":
                    subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/repomod/test_bench_suite.py"],
                                   cwd=ROOT, check=True)
                else:
                    render_preview()
    except (ValueError, subprocess.CalledProcessError) as error:
        print(f"bench: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
