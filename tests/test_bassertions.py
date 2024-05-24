from datetime import date
from decimal import Decimal, InvalidOperation
import pytest
from brightsidebudget import BAssertion


@pytest.mark.parametrize("d",
                         [{"Date": date(2016, 1, 1), "Account": "A", "Balance": 100},
                          {"Date": date(2016, 1, 1), "Account": "B", "Balance": 100.05},
                          {"Date": date(2016, 1, 1), "Account": "C", "Balance": -100},
                          {"Date": date(2016, 1, 1), "Account": "A", "Balance": 100,
                           "Include children": False},
                          {"Date": date(2016, 1, 1), "Account": "A", "Balance": 100,
                           "Include children": True}])
def test_from_dict(d: dict):
    b = BAssertion.from_dict(d)
    assert b.date() == d["Date"]
    assert b.account() == d["Account"]
    assert b.balance() == Decimal(str(d["Balance"]))
    assert b.include_children() is d.get("Include children", True)


@pytest.mark.parametrize("d",
                         [{"Date": True, "Account": "A", "Balance": 100},
                          {"Date": date(2016, 1, 1), "Account": "B", "Balance": "Hello"},
                          {"Account": "C", "Balance": -100},
                          {"Date": date(2016, 1, 1),  "Balance": 100,
                           "Include children": False},
                          {"Date": date(2016, 1, 1), "Account": "A"}])
def test_bad_from_dict(d: dict):
    with pytest.raises((ValueError, TypeError, InvalidOperation)):
        BAssertion.from_dict(d)
