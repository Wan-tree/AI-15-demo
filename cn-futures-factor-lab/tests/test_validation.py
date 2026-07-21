import pandas as pd
import pytest

from cn_futures_factor.data.synthetic import generate_synthetic_contract_daily
from cn_futures_factor.data.validation import validate_contract_daily
from cn_futures_factor.exceptions import DataValidationError


def test_synthetic_data_passes_contract() -> None:
    frame = generate_synthetic_contract_daily(periods=160, products=["RB"], seed=7)
    report = validate_contract_daily(frame)
    assert report.is_valid
    assert report.row_count == len(frame)


def test_duplicate_primary_key_is_rejected() -> None:
    frame = generate_synthetic_contract_daily(periods=160, products=["RB"], seed=7)
    duplicated = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    with pytest.raises(DataValidationError, match="重复"):
        validate_contract_daily(duplicated)


def test_inactive_ohlc_can_be_retained_as_an_explicit_warning() -> None:
    frame = generate_synthetic_contract_daily(periods=160, products=["RB"], seed=7)
    frame.loc[0, ["open", "high", "low", "close"]] = 0.0

    with pytest.raises(DataValidationError, match="OHLC"):
        validate_contract_daily(frame)

    report = validate_contract_daily(frame, allow_inactive_ohlc=True)
    assert report.is_valid
    assert any(issue.code == "inactive_or_invalid_ohlc" for issue in report.warnings)
