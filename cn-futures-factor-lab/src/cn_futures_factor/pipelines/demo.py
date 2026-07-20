"""无需外部数据即可运行的完整演示流水线。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from cn_futures_factor.backtest.engine import run_backtest
from cn_futures_factor.config import load_default_configs
from cn_futures_factor.data.storage import write_parquet_atomic
from cn_futures_factor.data.synthetic import generate_synthetic_contract_daily
from cn_futures_factor.data.validation import validate_contract_daily
from cn_futures_factor.evaluation.metrics import calculate_metrics
from cn_futures_factor.evaluation.report import save_equity_curve, write_markdown_report
from cn_futures_factor.features.pipeline import compute_features
from cn_futures_factor.futures.continuous import build_continuous_panel
from cn_futures_factor.futures.main_contract import build_main_contract_schedule
from cn_futures_factor.labels.forward_returns import add_forward_return_labels
from cn_futures_factor.models.baseline import IdentityFactorModel
from cn_futures_factor.paths import project_root
from cn_futures_factor.portfolio.construction import build_long_short_positions

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class DemoResult:
    """演示流水线重要输出路径和指标。"""

    report_path: Path
    chart_path: Path
    daily_path: Path
    positions_path: Path
    metrics: dict[str, float]


def run_demo(output_root: str | Path | None = None) -> DemoResult:
    """执行“生成数据 → 清洗校验 → 因子 → 组合 → 回测 → 报告”。

    ``output_root`` 主要用于自动测试，让测试可以把所有产物写入临时目录；普通用户
    不传时，产物会进入项目自己的 ``data/`` 和 ``artifacts/``。
    """

    configs = load_default_configs()
    base = configs["base"]
    root = Path(output_root).resolve() if output_root is not None else project_root()
    raw_directory = root / "data/raw"
    processed_directory = root / "data/processed"
    artifact_directory = root / "artifacts/demo"
    for directory in (raw_directory, processed_directory, artifact_directory):
        directory.mkdir(parents=True, exist_ok=True)

    demo_config = base["demo"]
    LOGGER.info("1/7 生成可重复的合成合约数据")
    contract_daily = generate_synthetic_contract_daily(
        start_date=demo_config["start_date"],
        periods=int(demo_config["periods"]),
        products=list(demo_config["products"]),
        contracts_per_product=int(demo_config["contracts_per_product"]),
        seed=int(base["project"]["random_seed"]),
    )
    raw_path = raw_directory / "demo_contract_daily.csv"
    contract_daily.to_csv(raw_path, index=False, encoding="utf-8-sig")

    LOGGER.info("2/7 校验标准数据契约")
    report = validate_contract_daily(contract_daily)
    LOGGER.info(report.summary())
    write_parquet_atomic(contract_daily, processed_directory / "demo_contract_daily.parquet")

    LOGGER.info("3/7 使用滞后持仓量选择主力合约")
    main_config = base["main_contract"]
    schedule = build_main_contract_schedule(
        contract_daily,
        selector=str(main_config["selector"]),
        selector_lag=int(main_config["selector_lag"]),
        prevent_delivery_month_rollback=bool(main_config["prevent_delivery_month_rollback"]),
    )
    panel = build_continuous_panel(schedule, contract_daily)
    write_parquet_atomic(panel, processed_directory / "demo_main_panel.parquet")

    LOGGER.info("4/7 计算基础因子和未来收益标签")
    features = compute_features(panel, configs["factors"])
    features = add_forward_return_labels(features)
    write_parquet_atomic(features, processed_directory / "demo_features.parquet")

    LOGGER.info("5/7 将基线因子转换为横截面多空权重")
    factor_name = str(configs["factors"]["signal_factor"])
    model = IdentityFactorModel(factor_name)
    features["prediction"] = model.predict(features)
    positions = build_long_short_positions(
        features[["trade_date", "product", "prediction"]],
        configs["backtest"]["portfolio"],
    )

    LOGGER.info("6/7 执行含调仓和换月成本的回测")
    result = run_backtest(positions, panel, configs["backtest"]["costs"])
    metrics = calculate_metrics(
        result.daily,
        annualization_days=int(configs["backtest"]["report"]["annualization_days"]),
    )

    LOGGER.info("7/7 保存研究产物")
    daily_path = artifact_directory / "daily_returns.csv"
    positions_path = artifact_directory / "positions.csv"
    chart_path = artifact_directory / "equity_curve.png"
    report_path = artifact_directory / "report.md"
    result.daily.to_csv(daily_path, index=False, encoding="utf-8-sig")
    result.positions.to_csv(positions_path, index=False, encoding="utf-8-sig")
    save_equity_curve(result.daily, chart_path)
    write_markdown_report(metrics, result.daily, report_path, factor_name=factor_name)

    return DemoResult(
        report_path=report_path,
        chart_path=chart_path,
        daily_path=daily_path,
        positions_path=positions_path,
        metrics=metrics,
    )
