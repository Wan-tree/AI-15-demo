import pandas as pd

from cn_futures_factor.futures.main_contract import build_main_contract_schedule


def test_main_contract_uses_previous_day_open_interest() -> None:
    dates = pd.to_datetime(["2026-01-05", "2026-01-06", "2026-01-07"])
    frame = pd.DataFrame(
        {
            "trade_date": list(dates) * 2,
            "product": ["RB"] * 6,
            "contract": ["RB2605"] * 3 + ["RB2610"] * 3,
            "open_interest": [100, 90, 80, 50, 200, 210],
        }
    ).sort_values(["contract", "trade_date"])

    schedule = build_main_contract_schedule(frame, selector_lag=1)
    selected = schedule.set_index("trade_date")["contract"].to_dict()

    # 1 月 6 日只能看到 1 月 5 日的持仓量，因此仍选择 RB2605。
    assert selected[pd.Timestamp("2026-01-06")] == "RB2605"
    # 1 月 7 日看到 1 月 6 日远月持仓量已经占优，才切换到 RB2610。
    assert selected[pd.Timestamp("2026-01-07")] == "RB2610"
