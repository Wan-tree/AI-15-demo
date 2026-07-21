"""可在合成数据或已标准化真实数据上运行的完整演示流水线。"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from cn_futures_factor.backtest.engine import run_backtest
from cn_futures_factor.config import load_default_configs
from cn_futures_factor.data.storage import write_parquet_atomic
from cn_futures_factor.data.synthetic import generate_synthetic_contract_daily
from cn_futures_factor.data.validation import validate_contract_daily
from cn_futures_factor.evaluation.metrics import calculate_metrics
from cn_futures_factor.evaluation.report import save_equity_curve, write_markdown_report
from cn_futures_factor.evaluation.robustness import (
    summarize_cost_scenarios,
    summarize_research_periods,
)
from cn_futures_factor.exceptions import ConfigurationError, DataValidationError
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

    data_source: str
    source_path: Path
    contract_daily_path: Path
    main_panel_path: Path
    features_path: Path
    report_path: Path
    chart_path: Path
    daily_path: Path
    positions_path: Path
    period_metrics_path: Path
    cost_scenarios_path: Path
    metrics: dict[str, float]


def _load_contract_daily(
    *,
    root: Path,
    data_source: str,
    input_path: str | Path | None,
    demo_config: dict[str, object],
    random_seed: int,
) -> tuple[pd.DataFrame, Path]:
    """按明确的数据源读取数据，避免真实数据和合成数据被悄悄混用。"""

    if data_source == "synthetic":
        contract_daily = generate_synthetic_contract_daily(
            start_date=str(demo_config["start_date"]),
            periods=int(demo_config["periods"]),
            products=list(demo_config["products"]),
            contracts_per_product=int(demo_config["contracts_per_product"]),
            seed=random_seed,
        )
        raw_directory = root / "data/raw"
        raw_directory.mkdir(parents=True, exist_ok=True)
        source_path = raw_directory / "demo_contract_daily.csv"
        contract_daily.to_csv(source_path, index=False, encoding="utf-8-sig")
        return contract_daily, source_path

    if data_source != "real":
        raise DataValidationError(
            f"未知演示数据源 {data_source!r}；只允许 'real' 或 'synthetic'"
        )

    configured_input = input_path or demo_config.get("real_input_path")
    if configured_input is None:
        raise DataValidationError("真实数据演示缺少输入路径，请配置 demo.real_input_path")
    source_path = Path(configured_input).expanduser()
    if not source_path.is_absolute():
        # 配置文件中的相对路径永远相对于项目根目录，而不是当前终端目录。
        source_path = project_root() / source_path
    source_path = source_path.resolve()
    if not source_path.exists():
        raise DataValidationError(
            f"标准化真实数据不存在：{source_path}；请先运行 cn-futures ingest"
        )
    if source_path.suffix.lower() != ".parquet":
        raise DataValidationError(
            "真实数据演示只读取已经过字段映射和 manifest 记录的 Parquet 文件"
        )
    return pd.read_parquet(source_path), source_path


def run_demo(
    output_root: str | Path | None = None,
    *,
    data_source: str | None = None,
    input_path: str | Path | None = None,
) -> DemoResult:
    """执行“读取数据 → 校验 → 因子 → 组合 → 回测 → 报告”。

    ``output_root`` 主要用于自动测试，让测试可以把所有产物写入临时目录；普通用户
    不传时，产物会进入项目自己的 ``data/`` 和 ``artifacts/``。``data_source`` 未显式
    指定时读取 ``configs/base.yaml``；当前项目默认使用已导入的真实数据，合成数据仅
    作为测试和离线兜底。
    """

    configs = load_default_configs()
    base = configs["base"]
    root = Path(output_root).resolve() if output_root is not None else project_root()
    processed_directory = root / "data/processed"
    demo_config = base["demo"]
    selected_source = str(data_source or demo_config.get("data_source", "synthetic")).lower()
    run_name = "real_demo" if selected_source == "real" else "demo"
    processed_prefix = "sufe" if selected_source == "real" else "demo"
    artifact_directory = root / f"artifacts/{run_name}"
    for directory in (processed_directory, artifact_directory):
        directory.mkdir(parents=True, exist_ok=True)

    LOGGER.info("1/7 读取 %s 合约数据", "真实" if selected_source == "real" else "合成")
    contract_daily, source_path = _load_contract_daily(
        root=root,
        data_source=selected_source,
        input_path=input_path,
        demo_config=demo_config,
        random_seed=int(base["project"]["random_seed"]),
    )

    LOGGER.info("2/7 校验标准数据契约")
    validation_report = validate_contract_daily(
        contract_daily,
        allow_inactive_ohlc=(
            selected_source == "real" and bool(demo_config.get("allow_inactive_ohlc", False))
        ),
    )
    LOGGER.info(validation_report.summary())
    contract_daily_path = write_parquet_atomic(
        contract_daily,
        processed_directory / f"{processed_prefix}_contract_daily.parquet",
    )

    LOGGER.info("3/7 使用滞后持仓量选择主力合约")
    main_config = base["main_contract"]
    schedule = build_main_contract_schedule(
        contract_daily,
        selector=str(main_config["selector"]),
        selector_lag=int(main_config["selector_lag"]),
        prevent_delivery_month_rollback=bool(main_config["prevent_delivery_month_rollback"]),
    )
    panel = build_continuous_panel(schedule, contract_daily)
    selected_zero_volume = int(panel["volume"].eq(0).sum())
    selected_zero_open_interest = int(panel["open_interest"].eq(0).sum())
    selected_nonpositive_ohlc = int(
        panel[["open", "high", "low", "close"]].le(0).any(axis=1).sum()
    )
    main_panel_path = write_parquet_atomic(
        panel,
        processed_directory / f"{processed_prefix}_main_panel.parquet",
    )

    LOGGER.info("4/7 计算基础因子和未来收益标签")
    execution_lag_days = int(configs["backtest"]["execution"]["signal_lag_days"])
    minimum_lagged_volume = float(
        configs["backtest"]["execution"].get("minimum_lagged_volume", 0.0)
    )
    minimum_lagged_open_interest = float(
        configs["backtest"]["execution"].get("minimum_lagged_open_interest", 0.0)
    )
    minimum_execution_volume = float(
        configs["backtest"]["execution"].get("minimum_execution_volume", 0.0)
    )
    require_positive_execution_ohlc = bool(
        configs["backtest"]["execution"].get("require_positive_execution_ohlc", False)
    )
    features = compute_features(panel, configs["factors"])
    features = add_forward_return_labels(
        features,
        execution_lag_days=execution_lag_days,
    )
    features_path = write_parquet_atomic(
        features,
        processed_directory / f"{processed_prefix}_features.parquet",
    )

    LOGGER.info("5/7 将基线因子转换为横截面多空权重")
    factor_name = str(configs["factors"]["signal_factor"])
    model = IdentityFactorModel(factor_name)
    features["prediction"] = model.predict(features)
    positions = build_long_short_positions(
        features[["trade_date", "product", "prediction"]],
        configs["backtest"]["portfolio"],
    )

    LOGGER.info("6/7 执行含调仓和换月成本的回测")
    result = run_backtest(
        positions,
        panel,
        configs["backtest"]["costs"],
        execution_lag_days=execution_lag_days,
        minimum_lagged_volume=minimum_lagged_volume,
        minimum_lagged_open_interest=minimum_lagged_open_interest,
        minimum_execution_volume=minimum_execution_volume,
        require_positive_execution_ohlc=require_positive_execution_ohlc,
    )
    annualization_days = int(configs["backtest"]["report"]["annualization_days"])
    metrics = calculate_metrics(
        result.daily,
        annualization_days=annualization_days,
    )
    period_metrics = summarize_research_periods(
        result.daily,
        configs["research"]["periods"],
        annualization_days=annualization_days,
    )
    base_costs = configs["backtest"]["costs"]
    scenario_base_costs = configs["backtest"]["cost_scenarios"].get("base")
    if scenario_base_costs is None or any(
        float(base_costs[key]) != float(scenario_base_costs[key])
        for key in ("rebalance_bps", "roll_bps")
    ):
        raise ConfigurationError("cost_scenarios.base 必须与回测使用的 costs 完全一致")
    cost_scenario_metrics = summarize_cost_scenarios(
        result.daily,
        configs["backtest"]["cost_scenarios"],
        annualization_days=annualization_days,
    )

    LOGGER.info("7/7 保存研究产物")
    daily_path = artifact_directory / "daily_returns.csv"
    positions_path = artifact_directory / "positions.csv"
    period_metrics_path = artifact_directory / "period_metrics.csv"
    cost_scenarios_path = artifact_directory / "cost_scenarios.csv"
    chart_path = artifact_directory / "equity_curve.png"
    report_path = artifact_directory / "report.md"
    result.daily.to_csv(daily_path, index=False, encoding="utf-8-sig")
    result.positions.to_csv(positions_path, index=False, encoding="utf-8-sig")
    period_metrics.to_csv(period_metrics_path, index=False, encoding="utf-8-sig")
    cost_scenario_metrics.to_csv(cost_scenarios_path, index=False, encoding="utf-8-sig")
    save_equity_curve(result.daily, chart_path)
    blocked_events = result.positions[
        result.positions["is_execution_event"] & ~result.positions["execution_eligible"]
    ]
    blocked_lagged = int(
        blocked_events["execution_exclusion_reason"].str.contains("lagged_").sum()
    )
    blocked_execution_day = int(
        blocked_events["execution_exclusion_reason"].str.contains("execution_").sum()
    )
    write_markdown_report(
        metrics,
        result.daily,
        report_path,
        factor_name=factor_name,
        data_source=selected_source,
        source_path=source_path,
        input_row_count=len(contract_daily),
        product_count=int(contract_daily["product"].nunique()),
        validation_summary=validation_report.summary(),
        data_quality_notes=[
            f"自行构造的主力面板共 {len(panel):,} 行，发生 {int(panel['is_roll_day'].sum()):,} 次换月。",
            f"主力面板中成交量为零 {selected_zero_volume:,} 行，持仓量为零 {selected_zero_open_interest:,} 行。",
            f"主力面板中 OHLC 非正 {selected_nonpositive_ohlc:,} 行；日期链仍保留，但执行层不允许这些记录形成成交仓位。",
            f"下单前使用昨日成交量≥{minimum_lagged_volume:g}、昨日持仓量≥{minimum_lagged_open_interest:g} 的统一准入门槛。",
            f"下单后要求执行日成交量≥{minimum_execution_volume:g} 且 OHLC 全部为正；只用于确认订单是否成交，不参与信号。",
            f"本次共有 {len(blocked_events):,} 个执行事件被阻止，其中 {blocked_lagged:,} 个触发滞后流动性规则、{blocked_execution_day:,} 个触发执行日规则（同一事件可同时触发）。",
        ],
        execution_lag_days=execution_lag_days,
        period_metrics=period_metrics,
        cost_scenario_metrics=cost_scenario_metrics,
        final_holdout_note=(
            "2025 年结果已在框架调试中被查看，不能再称为完全盲测；"
            + str(configs["research"]["final_holdout"]["rule"])
        ),
    )

    return DemoResult(
        data_source=selected_source,
        source_path=source_path,
        contract_daily_path=contract_daily_path,
        main_panel_path=main_panel_path,
        features_path=features_path,
        report_path=report_path,
        chart_path=chart_path,
        daily_path=daily_path,
        positions_path=positions_path,
        period_metrics_path=period_metrics_path,
        cost_scenarios_path=cost_scenarios_path,
        metrics=metrics,
    )
