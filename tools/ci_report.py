from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".work" / "ci-report"
RATE_RESERVE = 1500


def fleet_repositories() -> list[str]:
    output = subprocess.run(
        ["uv", "run", "repomod", "status", "--offline", "--include-private", "--json"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout
    return sorted(entry["repository"] for entry in json.loads(output))


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill fleet CI timings and build the offline report")
    parser.add_argument("--days", type=int, default=90, help="days of history to collect (default: 90)")
    args = parser.parse_args()
    if args.days < 1:
        parser.error("--days must be positive")

    report = Path(os.environ.get("CI_REPORT_REPO", Path.home() / "repos" / "github-actions-report"))
    cli = report / "src" / "cli.mts"
    if not cli.is_file():
        print(f"ci-report: missing {cli}", file=sys.stderr)
        return 2

    WORK.mkdir(parents=True, exist_ok=True)
    repos = WORK / "repos.txt"
    repos.write_text("".join(f"{name}\n" for name in fleet_repositories()), encoding="utf-8")
    data = WORK / "data"
    manifest = data / "fleet" / "manifest.json"
    if manifest.is_file():
        saved = json.loads(manifest.read_text(encoding="utf-8"))
        since, until = saved["since"], saved["until"]
    else:
        end = dt.datetime.now(dt.UTC).date()
        since, until = (end - dt.timedelta(days=args.days)).isoformat(), end.isoformat()
    subprocess.run(
        [
            "node", str(cli), "backfill", "--dataset=fleet", f"--repos-from={repos}",
            f"--since={since}", f"--until={until}", f"--rate-reserve={RATE_RESERVE}", f"--data={data}",
        ],
        cwd=report,
        check=True,
    )
    subprocess.run(
        ["node", str(cli), "build", "--dataset=fleet", f"--data={data}", f"--out={WORK / 'index.html'}"],
        cwd=report,
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
