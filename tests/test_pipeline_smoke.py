from pathlib import Path

import pandas as pd

from ekb_reliability.pipeline import ReliabilityPipeline


def test_pipeline_smoke(tmp_path: Path):
    df = pd.DataFrame(
        [
            {"Description": "CAP CER 0603 16V 10uF X6S +/-20%", "Manufacturer part number": "CL10X106MO8NRN", "Mfg name": "Samsung", "Qty": 2},
            {"Description": "CRYSTAL 12.0000MHZ 8PF SMD", "Manufacturer part number": "ABM8W-12.0000MHZ-8-D1X-T3", "Mfg name": "Abracon", "Qty": 1},
            {"Description": "SINGLE 3.3/5V RS232/RS422/RS485 MULTIPROTOCOL TRANSCEIVER 40-TQFN", "Manufacturer part number": "MAX3160E", "Mfg name": "Maxim", "Qty": 1},
        ]
    )
    path = tmp_path / "bom.csv"
    df.to_csv(path, index=False)

    pipe = ReliabilityPipeline()
    result = pipe.process_file(path)
    assert len(result.line_results) == 3
    assert result.summary["row_count"] == 3
