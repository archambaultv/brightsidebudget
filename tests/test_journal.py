from datetime import date
from decimal import Decimal
import pytest
from brightsidebudget.bassertion import BAssertion
from brightsidebudget.bsberror import BSBError
from brightsidebudget.posting import Posting
from brightsidebudget.account import Account
from brightsidebudget.txn import Txn
from brightsidebudget.journal import Journal


def test_journal__init__():
    j = Journal()
    assert j.accounts == []
    assert j.accounts_dict == {}
    assert j.bassertions == []
    assert j.txn_dict == {}
    assert j.postings == []


def test_add_account():
    j = Journal()
    a = Account(name="Test", number=1001, type="Actifs", group="Groupe", sub_group="Sous-groupe")
    j.add_account(a)
    assert j.accounts == [a]
    assert j.accounts_dict == {a.name: a}

    with pytest.raises(BSBError):
        j.add_account(a)


def test_add_bassertion():
    j = Journal()
    a = Account(name="Test", number=1001, type="Actifs", group="Groupe", sub_group="Sous-groupe")
    j.add_account(a)
    b = BAssertion(account=a, date=date(2025, 1, 1), balance=Decimal(100), comment="Comment")
    j.add_bassertion(b)
    assert j.bassertions == [b]

    with pytest.raises(BSBError):
        j.add_bassertion(b)


def test_add_txn():
    j = Journal()
    a1 = Account(name="Test", number=1001, type="Actifs", group="Groupe", sub_group="Sous-groupe")
    a2 = Account(name="Test2", number=1002, type="Actifs", group="Groupe", sub_group="Sous-groupe")
    j.add_account(a1)
    j.add_account(a2)
    p1 = Posting(txn_id=1, date=date(2025, 1, 1), account=a1, amount=Decimal(100),
                 comment="Comment", stmt_date=date(2025, 1, 1), stmt_desc="Desc")
    p2 = Posting(txn_id=1, date=date(2025, 1, 1), account=a2, amount=Decimal(-100),
                 comment="Comment2", stmt_date=date(2025, 1, 1), stmt_desc="Desc2")
    t = Txn(postings=[p1, p2])
    j.add_txn(t)
    assert len(j.txn_dict) == 1
    assert j.txn_dict[1].txn_id == 1
    assert j.txn_dict[1].date == date(2025, 1, 1)
    assert j.txn_dict[1].accounts() == [a1, a2]

    with pytest.raises(BSBError):
        a3 = Account(name="Test3", number=1003, type="Actifs", group="Groupe",
                     sub_group="Sous-groupe")
        p3 = Posting(txn_id=1, date=date(2025, 1, 1), account=a3, amount=Decimal(-100),
                     comment="Comment3", stmt_date=date(2025, 1, 1), stmt_desc="Desc3")
        t2 = Txn(postings=[p1, p3])
        j.add_txn(t2)


def test_balance_flow():
    j = Journal()
    a1 = Account(name="Test", number=1001, type="Actifs", group="Groupe", sub_group="Sous-groupe")
    a2 = Account(name="Test2", number=1002, type="Actifs", group="Groupe", sub_group="Sous-groupe")
    j.add_account(a1)
    j.add_account(a2)

    p1 = Posting(txn_id=1, date=date(2025, 1, 1), account=a1, amount=Decimal(100),
                 comment="Comment", stmt_date=date(2025, 1, 1), stmt_desc="Desc")
    p2 = Posting(txn_id=1, date=date(2025, 1, 1), account=a2, amount=Decimal(-100),
                 comment="Comment2", stmt_date=date(2025, 1, 1), stmt_desc="Desc2")
    t = Txn(postings=[p1, p2])
    j.add_txn(t)

    p1 = Posting(txn_id=2, date=date(2025, 1, 2), account=a1, amount=Decimal(100),
                 comment="Comment", stmt_date=date(2025, 1, 2), stmt_desc="Desc")
    p2 = Posting(txn_id=2, date=date(2025, 1, 2), account=a2, amount=Decimal(-100),
                 comment="Comment2", stmt_date=date(2025, 1, 2), stmt_desc="Desc2")
    t = Txn(postings=[p1, p2])
    j.add_txn(t)

    assert j.balance(account=a1, date=date(2025, 1, 1)) == 100
    assert j.balance(account=a2, date=date(2025, 1, 1)) == -100
    assert j.balance(account=a1, date=date(2025, 1, 2)) == 200
    assert j.balance(account=a2, date=date(2025, 1, 2)) == -200

    assert j.flow(account=a1, start_date=date(2025, 1, 1), end_date=date(2025, 1, 2)) == 200
    assert j.flow(account=a2, start_date=date(2025, 1, 1), end_date=date(2025, 1, 2)) == -200
    assert j.flow(account=a1, start_date=date(2025, 1, 2), end_date=date(2025, 1, 2)) == 100
    assert j.flow(account=a2, start_date=date(2025, 1, 2), end_date=date(2025, 1, 2)) == -100
