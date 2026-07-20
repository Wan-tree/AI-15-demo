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
