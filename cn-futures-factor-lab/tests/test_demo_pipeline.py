from pathlib import Path

import pandas as pd

from cn_futures_factor.pipelines.demo import run_demo


def test_demo_pipeline_runs_end_to_end(tmp_path: Path) -> None:
    result = run_demo(tmp_path)

    assert result.report_path.exists()
    assert result.chart_path.exists()
    assert result.daily_path.exists()
    assert result.positions_path.exists()
    daily = pd.read_csv(result.daily_path)
    assert len(daily) > 100
    assert daily["nav"].notna().all()
    assert result.metrics["max_drawdown"] <= 0
