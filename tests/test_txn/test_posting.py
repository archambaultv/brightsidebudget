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

def test_posting_renumber(account):
    p1 = Posting(
        txn_id=10,
        date=date(2024, 6, 12),
        account=account,
        amount=Decimal("1.00"),
        comment="",
        stmt_date=date(2024, 6, 12),
        stmt_desc=""
    )
    p2 = Posting(
        txn_id=12,
        date=date(2024, 6, 13),
        account=account,
        amount=Decimal("2.00"),
        comment="",
        stmt_date=date(2024, 6, 13),
        stmt_desc=""
    )
    p3 = Posting(
        txn_id=15,
        date=date(2024, 6, 14),
        account=account,
        amount=Decimal("3.00"),
        comment="",
        stmt_date=date(2024, 6, 14),
        stmt_desc=""
    )
    renumbered = Posting.renumber([p1, p2, p3])
    assert [p.txn_id for p in renumbered] == [1, 2, 3]
    assert renumbered[0].amount == Decimal("1.00")
    assert renumbered[1].amount == Decimal("2.00")
    assert renumbered[2].amount == Decimal("3.00")

def test_posting_renumber_empty():
    assert Posting.renumber([]) == []
