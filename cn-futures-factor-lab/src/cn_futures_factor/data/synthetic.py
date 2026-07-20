"""生成可重复的合成期货合约数据。

合成数据不是为了模拟真实收益，而是为了让任何同伴在没有数据库权限时也能验证工程
流程、主力换月、因子计算和回测接口。禁止用它得出真实投资结论。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ProductSpec:
    exchange: str
    initial_price: float
    annual_drift: float
    annual_volatility: float
    multiplier: float


DEFAULT_PRODUCT_SPECS: dict[str, ProductSpec] = {
    "RB": ProductSpec("SHFE", 3600.0, 0.03, 0.22, 10.0),
    "CU": ProductSpec("SHFE", 68000.0, 0.02, 0.18, 5.0),
    "M": ProductSpec("DCE", 3200.0, 0.025, 0.20, 10.0),
    "TA": ProductSpec("CZCE", 5400.0, 0.015, 0.21, 5.0),
    "SR": ProductSpec("CZCE", 6100.0, 0.01, 0.17, 10.0),
    "MA": ProductSpec("CZCE", 2500.0, 0.02, 0.24, 10.0),
}


def generate_synthetic_contract_daily(
    *,
    start_date: str = "2021-01-04",
    periods: int = 520,
    products: list[str] | tuple[str, ...] = ("RB", "CU", "M", "TA", "SR", "MA"),
    contracts_per_product: int = 4,
    seed: int = 42,
) -> pd.DataFrame:
    """生成具有重叠合约、成交量峰值和换月行为的日行情。

    每个品种共享一个平滑的“现货状态”，各月份合约根据剩余期限带有轻微升贴水。
    持仓量在合约生命周期中部达到峰值，使主力合约选择能够自然发生切换。
    """

    if periods < 120:
        raise ValueError("合成数据至少需要 120 个交易日，才能计算滚动因子")
    if contracts_per_product < 2:
        raise ValueError("至少需要两个合约，才能演示主力换月")

    dates = pd.bdate_range(start=start_date, periods=periods)
    random = np.random.default_rng(seed)
    records: list[dict[str, object]] = []

    for product in products:
        if product not in DEFAULT_PRODUCT_SPECS:
            raise ValueError(f"没有为合成品种 {product} 定义参数")
        spec = DEFAULT_PRODUCT_SPECS[product]

        # 所有月份合约共享这个基础价格过程；这样合约之间相关，但仍有期限升贴水。
        shocks = random.normal(
            loc=spec.annual_drift / 252,
            scale=spec.annual_volatility / np.sqrt(252),
            size=periods,
        )
        spot_path = spec.initial_price * np.exp(np.cumsum(shocks))

        for contract_index in range(contracts_per_product):
            expiry_index = 150 + contract_index * 130
            listing_index = max(0, expiry_index - 260)
            effective_expiry = min(expiry_index, periods - 1)
            if expiry_index < periods:
                expiry_date = dates[expiry_index]
            else:
                expiry_date = dates[-1] + pd.offsets.BDay(expiry_index - periods + 1)
            contract = f"{product}{expiry_date.year % 100:02d}{expiry_date.month:02d}"

            for index in range(listing_index, effective_expiry + 1):
                days_to_expiry = max(expiry_index - index, 0)
                carry = 0.025 * days_to_expiry / 252
                settlement = spot_path[index] * (1 + carry)

                # 用很小的随机波动构造合理的开高低收关系。
                intraday = abs(random.normal(0, spec.annual_volatility / np.sqrt(252)))
                open_price = settlement * (1 + random.normal(0, 0.002))
                close_price = settlement * (1 + random.normal(0, 0.0015))
                high = max(open_price, close_price, settlement) * (1 + intraday * 0.35)
                low = min(open_price, close_price, settlement) * (1 - intraday * 0.35)

                # 流动性随生命周期先上升后下降，并加入小幅噪声避免完全规则化。
                lifecycle_peak = np.exp(-(((days_to_expiry - 75) / 65) ** 2))
                volume = max(1, int(1500 + 85000 * lifecycle_peak + random.normal(0, 1200)))
                open_interest = max(1, int(3000 + 140000 * lifecycle_peak + random.normal(0, 1800)))
                turnover = volume * settlement * spec.multiplier

                records.append(
                    {
                        "trade_date": dates[index],
                        "exchange": spec.exchange,
                        "product": product,
                        "contract": contract,
                        "open": open_price,
                        "high": high,
                        "low": low,
                        "close": close_price,
                        "settlement": settlement,
                        "volume": float(volume),
                        "open_interest": float(open_interest),
                        "turnover": turnover,
                        "upper_limit": settlement * 1.08,
                        "lower_limit": settlement * 0.92,
                        "source": "synthetic_demo",
                    }
                )

    frame = pd.DataFrame.from_records(records).sort_values(
        ["contract", "trade_date"], kind="stable"
    )
    frame["pre_settlement"] = frame.groupby("contract", sort=False)["settlement"].shift(1)
    columns = [
        "trade_date",
        "exchange",
        "product",
        "contract",
        "open",
        "high",
        "low",
        "close",
        "settlement",
        "pre_settlement",
        "volume",
        "open_interest",
        "turnover",
        "upper_limit",
        "lower_limit",
        "source",
    ]
    return (
        frame[columns]
        .sort_values(["trade_date", "product", "contract"], kind="stable")
        .reset_index(drop=True)
    )
