import pandas as pd

from cn_futures_factor.config import load_yaml
from cn_futures_factor.data.synthetic import generate_synthetic_contract_daily
from cn_futures_factor.features.pipeline import compute_features
from cn_futures_factor.futures.continuous import build_continuous_panel
from cn_futures_factor.futures.main_contract import build_main_contract_schedule


def _feature_panel(raw: pd.DataFrame) -> pd.DataFrame:
    schedule = build_main_contract_schedule(raw)
    panel = build_continuous_panel(schedule, raw)
    return compute_features(panel, load_yaml("configs/factors.yaml"))


def test_future_rows_do_not_change_past_factor_values() -> None:
    raw = generate_synthetic_contract_daily(periods=240, products=["RB", "CU", "M"], seed=17)
    cutoff = pd.Timestamp(sorted(raw["trade_date"].unique())[179])
    truncated = raw[raw["trade_date"] <= cutoff].copy()

    full_features = _feature_panel(raw)
    truncated_features = _feature_panel(truncated)
    columns = ["trade_date", "product", "momentum_20", "volatility_20"]
    left = full_features.loc[full_features["trade_date"] <= cutoff, columns].reset_index(drop=True)
    right = truncated_features[columns].reset_index(drop=True)

    pd.testing.assert_frame_equal(left, right, check_exact=False, rtol=1e-12, atol=1e-12)
