"""数据质量检查。

金融研究最危险的错误往往不会触发程序崩溃，而是悄悄产生一个看似漂亮的结果。
本模块将基础数据约束变成自动检查，并把错误和警告分开记录。
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from cn_futures_factor.data.schema import REQUIRED_CONTRACT_DAILY_COLUMNS
from cn_futures_factor.exceptions import DataValidationError


@dataclass(frozen=True)
class ValidationIssue:
    """单条质量问题。``severity`` 只能是 error 或 warning。"""

    severity: str
    code: str
    message: str
    count: int = 0


@dataclass
class ValidationReport:
    """一次数据检查的结构化结果。"""

    row_count: int
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def summary(self) -> str:
        """生成适合日志和命令行展示的中文摘要。"""

        if not self.issues:
            return f"数据检查通过，共 {self.row_count:,} 行。"
        lines = [
            f"数据检查完成：{self.row_count:,} 行，{len(self.errors)} 个错误，{len(self.warnings)} 个警告。"
        ]
        for issue in self.issues:
            lines.append(f"- [{issue.severity}] {issue.code}: {issue.message} (数量={issue.count})")
        return "\n".join(lines)


def validate_contract_daily(
    frame: pd.DataFrame,
    *,
    raise_on_error: bool = True,
) -> ValidationReport:
    """检查标准合约日行情表。

    参数
    ----
    frame:
        已完成字段标准化的数据。
    raise_on_error:
        为真时，只要存在严重错误就抛出 ``DataValidationError``。探索阶段可以传假，
        先查看完整报告再决定如何修复。
    """

    report = ValidationReport(row_count=len(frame))
    missing = [column for column in REQUIRED_CONTRACT_DAILY_COLUMNS if column not in frame]
    if missing:
        report.issues.append(
            ValidationIssue("error", "missing_columns", f"缺少必要字段：{missing}", len(missing))
        )
        if raise_on_error:
            raise DataValidationError(report.summary())
        return report

    if frame.empty:
        report.issues.append(ValidationIssue("error", "empty_data", "数据表为空", 0))

    invalid_dates = int(frame["trade_date"].isna().sum())
    if invalid_dates:
        report.issues.append(
            ValidationIssue("error", "invalid_dates", "存在无法解析的交易日期", invalid_dates)
        )

    duplicate_rows = int(frame.duplicated(["trade_date", "contract"]).sum())
    if duplicate_rows:
        report.issues.append(
            ValidationIssue(
                "error",
                "duplicate_primary_key",
                "交易日期与合约代码组合重复",
                duplicate_rows,
            )
        )

    missing_identity = int(frame[["exchange", "product", "contract"]].isna().any(axis=1).sum())
    if missing_identity:
        report.issues.append(
            ValidationIssue(
                "error", "missing_identity", "交易所、品种或合约代码为空", missing_identity
            )
        )

    price_columns = ["open", "high", "low", "close", "settlement"]
    invalid_price = int(
        (frame[price_columns].le(0) | frame[price_columns].isna()).any(axis=1).sum()
    )
    if invalid_price:
        report.issues.append(
            ValidationIssue("error", "invalid_price", "核心价格为空、为零或为负", invalid_price)
        )

    invalid_range = int(
        (
            (frame["high"] < frame["low"])
            | (frame["high"] < frame[["open", "close"]].max(axis=1))
            | (frame["low"] > frame[["open", "close"]].min(axis=1))
        ).sum()
    )
    if invalid_range:
        report.issues.append(
            ValidationIssue("error", "invalid_ohlc_range", "OHLC 价格区间不一致", invalid_range)
        )

    negative_activity = int((frame[["volume", "open_interest"]] < 0).any(axis=1).sum())
    if negative_activity:
        report.issues.append(
            ValidationIssue("error", "negative_activity", "成交量或持仓量为负", negative_activity)
        )

    zero_activity = int((frame[["volume", "open_interest"]] == 0).any(axis=1).sum())
    if zero_activity:
        report.issues.append(
            ValidationIssue("warning", "zero_activity", "部分记录成交量或持仓量为零", zero_activity)
        )

    if raise_on_error and not report.is_valid:
        raise DataValidationError(report.summary())
    return report
