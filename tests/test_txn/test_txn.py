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

def test_txn_split_into_pairs():
    p1 = make_posting(txn_id=1, amount=Decimal("-50"), account=make_account(name="A"))
    p2 = make_posting(txn_id=1, amount=Decimal("10"), account=make_account(name="B"))
    p3 = make_posting(txn_id=1, amount=Decimal("20"), account=make_account(name="C"))
    p4 = make_posting(txn_id=1, amount=Decimal("20"), account=make_account(name="D"))
    txns = Txn.split_into_pairs([Txn(postings=[p1, p2, p3, p4])])
    assert len(txns) == 3
    for i, txn in enumerate(txns):
        assert txn.txn_id == 2 + i
    for i, p in enumerate([p2, p3, p4]):
        t = txns[i]
        assert len(t.postings) == 2
        assert t.postings[0].amount == -p.amount
        assert t.postings[1].amount == p.amount

def test_txn_split_into_pairs_failed():
    p1 = make_posting(txn_id=1, amount=Decimal("-50"), account=make_account(name="A"))
    p2 = make_posting(txn_id=1, amount=Decimal("10"), account=make_account(name="B"))
    p3 = make_posting(txn_id=1, amount=Decimal("-10"), account=make_account(name="C"))
    p4 = make_posting(txn_id=1, amount=Decimal("50"), account=make_account(name="D"))
    with pytest.raises(ValueError):
        Txn.split_into_pairs([Txn(postings=[p1, p2, p3, p4])])

def test_move_opening_balance_date():
    balance_account = make_account(name="Solde d'ouverture", type_name="Capitaux propres", number=3000)
    p1 = make_posting(txn_id=1, amount=Decimal("-50"), account=make_account(name="A", type_name="Actifs"))
    p2 = make_posting(txn_id=1, amount=Decimal("30"), account=make_account(name="B", type_name="Actifs"))
    p3 = make_posting(txn_id=1, amount=Decimal("-10"), account=make_account(name="C", type_name="Passifs", number=2000))
    p4 = make_posting(txn_id=1, amount=Decimal("50"), account=balance_account)
    p5 = make_posting(txn_id=1, amount=Decimal("60"), account=make_account(name="E", type_name="Revenus", number=4000))
    p6 = make_posting(txn_id=1, amount=Decimal("-90"), account=make_account(name="F", type_name="Dépenses", number=5000))
    p7 = make_posting(txn_id=1, amount=Decimal("10"),account=make_account(name="A", type_name="Actifs"))
    t = Txn(postings=[p1, p2, p3, p4, p5, p6, p7])

    p8 = make_posting(txn_id=2, date=datetime.date(2024,1,2), amount=Decimal("60"),
                      account=make_account(name="E", type_name="Revenus", number=4000))
    p9 = make_posting(txn_id=2, date=datetime.date(2024,1,2), amount=Decimal("-60"),
                      account=make_account(name="F", type_name="Dépenses", number=5000))
    t2 = Txn(postings=[p8, p9])  # Transaction with balance account and others
    tnxs = Txn.move_opening_balance_date(
        txns=[t, t2],
        opening_balance_date=datetime.date(2024, 1, 2),
        opening_balance_account=balance_account
    )
    assert len(tnxs) == 4
    for txn in tnxs:
        assert txn.date == datetime.date(2024, 1, 2)
    assert tnxs[0].postings[0].account.name == "E"
    assert tnxs[0].postings[0].amount == Decimal("60")
    assert tnxs[0].postings[1].account.name == "F"
    assert tnxs[0].postings[1].amount == Decimal("-60")
    assert tnxs[1].postings[0].account.name == "A"
    assert tnxs[1].postings[0].amount == Decimal("-40")
    assert tnxs[1].postings[1].account.name == balance_account.name
    assert tnxs[2].postings[0].account.name == "B"
    assert tnxs[2].postings[0].amount == Decimal("30")
    assert tnxs[2].postings[1].account.name == balance_account.name
    assert tnxs[3].postings[0].account.name == "C"
    assert tnxs[3].postings[0].amount == Decimal("-10")
    assert tnxs[3].postings[1].account.name == balance_account.name