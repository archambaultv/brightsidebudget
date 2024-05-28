from datetime import date
from decimal import Decimal
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
    assert p.account() == "A"
    assert p.amount() == d["Amount"]
    assert p.txn() == 1
    assert p.date() == date(2021, 1, 1)
    assert p.get_dict() == d


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
