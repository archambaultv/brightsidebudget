import pytest
from decimal import Decimal
from datetime import date
from brightsidebudget.txn.posting import Posting
from brightsidebudget.account.account import Account
from brightsidebudget.account.account_type import AccountType

@pytest.fixture
def account():
    atype = AccountType(name="Actifs")
    return Account(name="Banque", type=atype, number=1001, group="Courant", subgroup="Banque principale")

def test_posting_init(account):
    p = Posting(
        txn_id=1,
        date=date(2024, 6, 1),
        account=account,
        amount=Decimal("100.50"),
        comment="Test",
        stmt_date=date(2024, 6, 2),
        stmt_desc="Relevé"
    )
    assert p.txn_id == 1
    assert p.date == date(2024, 6, 1)
    assert p.account == account
    assert p.amount == Decimal("100.50")
    assert p.comment == "Test"
    assert p.stmt_date == date(2024, 6, 2)
    assert p.stmt_desc == "Relevé"

def test_posting_init2(account):
    p = Posting(
        txn_id=1,
        date=date(2024, 6, 1),
        account=account,
        amount=Decimal("100.50")
    )
    assert p.txn_id == 1
    assert p.date == date(2024, 6, 1)
    assert p.account == account
    assert p.amount == Decimal("100.50")
    assert p.comment == ""
    assert p.stmt_date == date(2024, 6, 1)
    assert p.stmt_desc == ""


def test_posting_dedup_key(account):
    p = Posting(
        txn_id=7,
        date=date(2024, 6, 10),
        account=account,
        amount=Decimal("77.77"),
        comment="",
        stmt_date=date(2024, 6, 10),
        stmt_desc="desc"
    )
    assert p.dedup_key() == (date(2024, 6, 10), "Banque", Decimal("77.77"), "desc")

def test_posting_sort_key(account):
    p = Posting(
        txn_id=8,
        date=date(2024, 6, 11),
        account=account,
        amount=Decimal("88.88"),
        comment="",
        stmt_date=date(2024, 6, 11),
        stmt_desc=""
    )
    assert p.sort_key() == (date(2024, 6, 11), 1001, 8)
