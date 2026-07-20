import pytest

from cn_futures_factor.exceptions import DataValidationError
from cn_futures_factor.futures.contracts import parse_contract_code


def test_parse_four_digit_contract_with_exchange_suffix() -> None:
    info = parse_contract_code("rb2610.SHFE")
    assert info.product == "RB"
    assert info.delivery_yyyymm == 202610


def test_parse_three_digit_contract_uses_reference_year() -> None:
    info = parse_contract_code("MA409", "2024-02-01")
    assert info.product == "MA"
    assert info.delivery_yyyymm == 202409


def test_invalid_delivery_month_fails_loudly() -> None:
    with pytest.raises(DataValidationError):
        parse_contract_code("RB2613")
