from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("program", "error_location"),
    [
        pytest.param(
            'from repomod.dependencies.enrich import _table\n\n_table({"source": 123})["source"].strip()\n',
            "3:1",
            id="registry-table",
        ),
        pytest.param(
            "from pathlib import Path\n"
            "from repomod.rules.build_repos import _lock_document\n"
            "from repomod.types import Repository\n\n"
            "def misuse(root: Path, repository: Repository) -> None:\n"
            '    document, _ = _lock_document(root, repository, "sources.lock.json", required=True)\n'
            "    if document is not None:\n"
            '        document["schema_version"].strip()\n',
            "8:9",
            id="build-lock",
        ),
    ],
)
def test_unknown_dependency_values_require_narrowing(tmp_path: Path, program: str, error_location: str) -> None:
    root = Path(__file__).resolve().parents[2]
    witness = tmp_path / "invalid_lookup.py"
    witness.write_text(program, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "ty", "check", str(witness), "--extra-search-path", str(root),
         "--output-format", "concise"],
        cwd=root, capture_output=True, text=True, timeout=20, check=False,
    )

    diagnostics = result.stdout + result.stderr
    assert result.returncode == 1, diagnostics
    assert diagnostics.count("error[") == 1, diagnostics
    assert f"invalid_lookup.py:{error_location}: error[missing-attribute]" in diagnostics
    assert "Object of type `object` has no attribute `strip`" in diagnostics
