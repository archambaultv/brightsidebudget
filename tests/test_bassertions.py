from datetime import date
from decimal import Decimal, InvalidOperation
import pytest
from brightsidebudget import BAssertion


@pytest.mark.parametrize("d",
                         [{"Date": date(2016, 1, 1), "Account": "A", "Balance": 100},
                          {"Date": "2016-01-01", "Account": "A", "Balance": 100},
                          {"Date": "2016-01-01", "Account": "A", "Balance": "100"},
                          {"Date": date(2016, 1, 1), "Account": "B", "Balance": 100.05},
                          {"Date": date(2016, 1, 1), "Account": "C", "Balance": -100},
                          {"Date": date(2016, 1, 1), "Account": "A", "Balance": 100,
                           "Include children": False},
                          {"Date": date(2016, 1, 1), "Account": "A", "Balance": 100.1,
                           "Include children": "False"},
                          {"Date": date(2016, 1, 1), "Account": "A", "Balance": 100,
                           "Include children": True}])
def test_from_dict(d: dict):
    b = BAssertion.from_dict(d, copy=True)
    d["Balance"] = Decimal(str(d["Balance"]))
    d["Date"] = date(2016, 1, 1)
    if "Include children" not in d:
        d["Include children"] = True
    else:
        if d["Include children"] in ["False", "True"]:
            d["Include children"] = d["Include children"] == "True"
    assert b.date == d["Date"]
    assert isinstance(b.date, date)
    assert b.account == d["Account"]
    assert isinstance(b.account, str)
    assert b.balance == d["Balance"]
    assert isinstance(b.balance, Decimal)
    assert isinstance(b.include_children, bool)
    assert b.include_children == d["Include children"]
    assert b.get_dict() == d


def test_get_set():
    b = BAssertion(date=date(2016, 1, 1), account="A", balance=100)
    assert b.account == "A"
    assert b.balance == Decimal("100")
    assert b.date == date(2016, 1, 1)
    assert b.include_children is True
    b.account = "B"
    b.balance = Decimal("200")
    b.date = "2016-01-02"
    b.include_children = False
    assert b.account == "B"
    assert b.balance == Decimal("200")
    assert b.date == date(2016, 1, 2)
    assert b.include_children is False
    b["Account"] = "C"
    b["Balance"] = 300
    b["Date"] = "2016-01-03"
    b["Include children"] = "True"
    assert b.account == "C"
    assert b.balance == Decimal("300")
    assert b.date == date(2016, 1, 3)
    assert b.include_children is True

    with pytest.raises(ValueError):
        b.account = ""

    with pytest.raises(ValueError):
        b["Account"] = ""

    with pytest.raises(ValueError):
        b.account = 125

    with pytest.raises(ValueError):
        b["Account"] = 125

    with pytest.raises(InvalidOperation):
        b.balance = "Hello"

    with pytest.raises(InvalidOperation):
        b["Balance"] = "Hello"

    with pytest.raises(ValueError):
        b.date = "Hello"

    with pytest.raises(ValueError):
        b["Date"] = "Hello"


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
