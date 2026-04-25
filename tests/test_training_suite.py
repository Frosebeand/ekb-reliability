from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_training_suite_without_classifier_dataset(tmp_path):
    output_root = tmp_path / "suite"
    cmd = [
        sys.executable,
        "-m",
        "ekb_reliability.ml.run_training_suite",
        "--output-root",
        str(output_root),
        "--regression-samples",
        "80",
        "--bom-file",
        "data/sample_bom.csv",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path.cwd() / "src") + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads((output_root / "training_suite_summary.json").read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert len(payload["steps"]) == 4
