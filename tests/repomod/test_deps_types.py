from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_unknown_enrichment_values_require_narrowing(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    witness = tmp_path / "invalid_lookup.py"
    witness.write_text(
        'from repomod.dependencies.enrich import _table\n\n_table({"source": 123})["source"].strip()\n',
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-m", "ty", "check", str(witness), "--extra-search-path", str(root),
         "--output-format", "concise"],
        cwd=root, capture_output=True, text=True, timeout=20, check=False,
    )

    diagnostics = result.stdout + result.stderr
    assert result.returncode == 1, diagnostics
    assert diagnostics.count("error[") == 1, diagnostics
    assert "invalid_lookup.py:3:1: error[missing-attribute]" in diagnostics
    assert "Object of type `object` has no attribute `strip`" in diagnostics
