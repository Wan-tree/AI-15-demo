from pathlib import Path

import pandas as pd

from cn_futures_factor.data.synthetic import generate_synthetic_contract_daily
from cn_futures_factor.pipelines.demo import run_demo


def test_demo_pipeline_runs_end_to_end(tmp_path: Path) -> None:
    result = run_demo(tmp_path, data_source="synthetic")

    assert result.report_path.exists()
    assert result.chart_path.exists()
    assert result.daily_path.exists()
    assert result.positions_path.exists()
    assert result.period_metrics_path.exists()
    assert result.cost_scenarios_path.exists()
    daily = pd.read_csv(result.daily_path)
    assert len(daily) > 100
    assert daily["nav"].notna().all()
    assert result.metrics["max_drawdown"] <= 0


def test_real_data_path_uses_the_same_pipeline_without_generating_raw_data(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "standardized_real_sample.parquet"
    sample = generate_synthetic_contract_daily(periods=160, products=["RB", "CU", "M"], seed=9)
    sample["source"] = "authorized_export_test_sample"
    sample.to_parquet(input_path, index=False)

    result = run_demo(tmp_path, data_source="real", input_path=input_path)

    assert result.data_source == "real"
    assert result.source_path == input_path.resolve()
    assert result.report_path.parent.name == "real_demo"
    assert result.contract_daily_path.name == "sufe_contract_daily.parquet"
    assert not (tmp_path / "data/raw/demo_contract_daily.csv").exists()
    assert "真实数据基础演示" in result.report_path.read_text(encoding="utf-8")
