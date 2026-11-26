"""End-to-end test on the synthetic sample: the pipeline runs and catches the planted events."""
import subprocess
import sys

import pandas as pd

from src import config
from src.run_pipeline import run


def test_pipeline_on_sample(tmp_path):
    subprocess.run([sys.executable, "scripts/make_sample_data.py"], check=True, cwd=config.ROOT)
    out = run("sample", report_dir=tmp_path, db_path=tmp_path / "test.duckdb")

    daily = out["daily"]
    assert len(daily) == (pd.Timestamp(config.ANALYSIS_END) - pd.Timestamp(config.ANALYSIS_START)).days + 1
    assert (daily["gmv"] >= 0).all()

    alerts = out["anomalies"].assign(dt=lambda d: pd.to_datetime(d["dt"]).dt.strftime("%Y-%m-%d"))
    flagged = set(zip(alerts["dt"], alerts["metric"], alerts["direction"]))
    assert ("2017-11-24", "gmv", "up") in flagged          # planted Black Friday spike
    assert ("2018-05-15", "orders", "down") in flagged     # planted outage

    dec = out["campaign"]["decomposition"]
    assert abs(dec["share_of_gmv_change"].sum() - 1) < 1e-9  # log decomposition adds up

    assert (tmp_path / "summary.md").exists()
    assert (tmp_path / "figures" / "daily_gmv_alerts.svg").exists()
