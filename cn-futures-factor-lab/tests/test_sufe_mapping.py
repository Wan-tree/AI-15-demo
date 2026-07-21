import pandas as pd

from cn_futures_factor.config import load_yaml
from cn_futures_factor.data.normalization import standardize_contract_daily


def test_sufe_integer_date_and_exchange_are_standardized() -> None:
    raw = pd.DataFrame(
        {
            "trade_date": [20200102, 20200103],
            "exchange": ["上海", "上海"],
            "variety": ["SC", "SC"],
            "contract_code": ["SC2003", "SC2003"],
            "open": [480.0, 481.0],
            "high": [482.0, 483.0],
            "low": [479.0, 480.0],
            "close": [481.0, 482.0],
            "settle_price": [480.5, 481.5],
            "volume": [100, 120],
            "open_interest": [200, 210],
            "amount": [1000.0, 1200.0],
        }
    )
    mapping = load_yaml("configs/field_mappings_sufe_all_contracts.yaml")

    result = standardize_contract_daily(raw, mapping, source_name="test_sufe")

    assert result["trade_date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2020-01-02",
        "2020-01-03",
    ]
    assert result["product"].tolist() == ["SC", "SC"]
    assert result["contract"].tolist() == ["SC2003", "SC2003"]
    assert result["exchange"].tolist() == ["INE", "INE"]
    assert pd.isna(result.loc[0, "pre_settlement"])
    assert result.loc[1, "pre_settlement"] == 480.5
