from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def command(action: str, **values: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({"TIER": "edit", "WORKLOAD": "", "ALLOW_FULL": ""})
    env.update(values)
    return subprocess.run([sys.executable, "bench/suite.py", action], cwd=ROOT, env=env,
                          capture_output=True, text=True, check=False)


def test_selection_and_full_guard() -> None:
    result = command("check", TIER="change")
    assert result.returncode == 0
    assert "selected: selection" in result.stdout
    assert "selected: preview-render" in result.stdout
    assert command("check", TIER="full").returncode != 0
    assert command("check", WORKLOAD="missing").returncode != 0
    assert command("check", WORKLOAD="preview-render").returncode != 0


def test_preflight_fails_before_running_workload(monkeypatch, tmp_path: Path) -> None:
    from bench import suite

    monkeypatch.setattr(suite, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="missing inputs"):
        suite.preflight(["preview-render"])
    assert not list(tmp_path.iterdir())
