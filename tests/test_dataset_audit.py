from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_dataset_audit_cli(tmp_path):
    output_dir = tmp_path / "audit"
    cmd = [
        sys.executable,
        "-m",
        "ekb_reliability.ml.dataset_audit",
        "--output-dir",
        str(output_dir),
        "--regression-samples",
        "50",
        "--bom-file",
        "data/sample_bom.csv",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path.cwd() / "src") + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads((output_dir / "dataset_audit.json").read_text(encoding="utf-8"))
    assert payload["regression_dataset"]["rows"] == 50
    assert (output_dir / "dataset_audit.md").exists()
