import pytest
from decimal import Decimal
from brightsidebudget.txn.txn import Txn
from brightsidebudget.txn.posting import Posting
from brightsidebudget.account.account import Account
from brightsidebudget.account.account_type import AccountType
import datetime

def make_account(name="A", type_name="Actifs", number=1001):
    return Account(
        name=name,
        type=AccountType(name=type_name), # type: ignore
        number=number,
        group="G",
        subgroup="SG"
    )

def make_posting(txn_id=1, date=None, account=None, amount=Decimal("10")):
    if date is None:
        date = datetime.date(2024, 1, 1)
    if account is None:
        account = make_account()
    return Posting(
        txn_id=txn_id,
        date=date,
        account=account,
        amount=amount
    )

def test_txn_init_valid():
    p1 = make_posting(amount=Decimal("10"))
    p2 = make_posting(amount=Decimal("-10"))
    txn = Txn(postings=[p1, p2])
    assert txn.txn_id == 1
    assert txn.date == p1.date
    assert txn.postings == [p1, p2]

def test_txn_init_invalid_txn_id():
    p1 = make_posting(txn_id=1)
    p2 = make_posting(txn_id=2)
    with pytest.raises(ValueError):
        Txn(postings=[p1, p2])

def test_txn_init_invalid_date():
    p1 = make_posting(date=datetime.date(2024, 1, 1))
    p2 = make_posting(date=datetime.date(2024, 1, 2))
    with pytest.raises(ValueError):
        Txn(postings=[p1, p2])

def test_txn_init_not_balanced():
    p1 = make_posting(amount=Decimal("10"))
    p2 = make_posting(amount=Decimal("5"))
    with pytest.raises(ValueError):
        Txn(postings=[p1, p2])

def test_txn_accounts_sorted():
    acc1 = make_account(name="B", number=1002)
    acc2 = make_account(name="A", number=1001)
    p1 = make_posting(account=acc1, amount=Decimal("10"))
    p2 = make_posting(account=acc2, amount=Decimal("-10"))
    txn = Txn(postings=[p1, p2])
    accounts = txn.accounts()
    assert accounts[0].name == "A"
    assert accounts[1].name == "B"

def test_txn_is_uncategorized_true():
    acc = make_account(type_name="Non classé", number=6001)
    p1 = make_posting(account=acc, amount=Decimal("10"))
    p2 = make_posting(amount=Decimal("-10"))
    txn = Txn(postings=[p1, p2])
    assert txn.is_uncategorized() is True

def test_txn_is_uncategorized_false():
    p1 = make_posting(amount=Decimal("10"))
    p2 = make_posting(amount=Decimal("-10"))
    txn = Txn(postings=[p1, p2])
    assert txn.is_uncategorized() is False

def test_txn_from_postings():
    p1 = make_posting(txn_id=1, amount=Decimal("10"), account=make_account(name="A"))
    p2 = make_posting(txn_id=1, amount=Decimal("-10"), account=make_account(name="B"))
    p3 = make_posting(txn_id=2, amount=Decimal("20"), account=make_account(name="C"))
    p4 = make_posting(txn_id=2, amount=Decimal("-20"), account=make_account(name="D"))
    txns = Txn.from_postings([p1, p2, p3, p4])
    assert len(txns) == 2
    assert txns[0].txn_id == 1
    assert txns[1].txn_id == 2
    assert all(isinstance(t, Txn) for t in txns)