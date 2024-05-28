from datetime import date
from decimal import Decimal, InvalidOperation
from pydantic import ValidationError
import pytest
from brightsidebudget import Posting


@pytest.mark.parametrize("d",
                         [{"Txn": 1, "Date": "2021-01-01", "Account": "A", "Amount": 100},
                          {"Txn": "1", "Date": date(2021, 1, 1), "Account": "A", "Amount": -100,
                           "desc": "My transaction"},
                          {"Txn": 1, "Date": "2021-01-01", "Account": "A", "Amount": "100.04",
                           "date2": date(2021, 1, 1)},
                          {"Txn": 1, "Date": "2021-01-01", "Account": "A",
                           "Amount": 100.0145, "date2": date(2021, 1, 1), "payee": "ABC Corp"},
                          {"Txn": 1, "Date": "2021-01-01", "Account": "A", "Amount": 100,
                           "date2": date(2021, 1, 1)}])
def test_posting_from_dict(d: dict):
    p = Posting.from_dict(d, copy=True)
    d["Amount"] = Decimal(str(d["Amount"]))
    d["Date"] = date(2021, 1, 1)
    d["Txn"] = int(d["Txn"])
    assert p.account == "A"
    assert p.amount == d["Amount"]
    assert p.txn == 1
    assert p.date == date(2021, 1, 1)
    assert p.get_dict() == d


def test_get_set():
    p = Posting(txn=1, account="A", date="2021-01-01", amount=100)
    assert p.account == "A"
    assert p.amount == Decimal("100")
    assert p.date == date(2021, 1, 1)
    assert p.txn == 1
    p.account = "B"
    p.amount = "200"
    p.date = "2021-01-02"
    p.txn = 2
    assert p.account == "B"
    assert p.amount == Decimal("200")
    assert p.date == date(2021, 1, 2)
    assert p.txn == 2
    p["Account"] = "C"
    p["Amount"] = 300
    p["Date"] = "2021-01-03"
    p["Txn"] = 3
    assert p.account == "C"
    assert p.amount == Decimal("300")
    assert p.date == date(2021, 1, 3)
    assert p.txn == 3

    with pytest.raises(ValueError):
        p.account = ""

    with pytest.raises(ValueError):
        p["Account"] = ""

    with pytest.raises(ValueError):
        p.account = 125

    with pytest.raises(ValueError):
        p["Account"] = 125

    with pytest.raises(InvalidOperation):
        p.amount = "Hello"

    with pytest.raises(InvalidOperation):
        p["Amount"] = "Hello"

    with pytest.raises(TypeError):
        p.date = 10.5

    with pytest.raises(TypeError):
        p["Date"] = 10.5


@pytest.mark.parametrize("d",
                         [{"Date": "2021-01-01", "Account": "A", "Amount": 100},
                          {"Txn": "1", "Account": "A", "Amount": -100,
                           "desc": "My transaction"},
                          {"Txn": 1, "Date": "2021-01-01", "Amount": 100.04},
                          {"Txn": 1, "Date": "2021-01-01", "Account": "A"},
                          {"Txn": "Hello", "Date": "2021-01-01", "Account": "A", "Amount": 100}])
def test_bad_from_dict(d: dict):
    with pytest.raises((ValidationError, ValueError)):
        Posting.from_dict(d)
