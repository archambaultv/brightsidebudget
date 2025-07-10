import pytest
from datetime import date
from decimal import Decimal
from brightsidebudget.journal import Journal
from brightsidebudget.account.account import Account
from brightsidebudget.bassertion import BAssertion
from brightsidebudget.txn.posting import Posting
from brightsidebudget.txn.txn import Txn

@pytest.fixture
def sample_accounts():
    return [
        Account(name="Cash", number=1000, type="Actifs"),  # type: ignore
        Account(name="Bank", number=1200, type="Actifs")  # type: ignore
    ]

@pytest.fixture
def sample_postings(sample_accounts):
    return [
        Posting(txn_id=1, account=sample_accounts[0], amount=Decimal("100.00"), date=date(2023, 1, 1)),
        Posting(txn_id=1, account=sample_accounts[0], amount=Decimal("-30.00"), date=date(2023, 1, 1)),
        Posting(txn_id=1, account=sample_accounts[1], amount=Decimal("-70.00"), date=date(2023, 1, 1)),
    ]

@pytest.fixture
def sample_txns(sample_postings):
    return [
        Txn(postings=sample_postings)
    ]

@pytest.fixture
def sample_bassertions(sample_accounts):
    return [
        BAssertion(account=sample_accounts[0], date=date(2023, 1, 1), balance=Decimal("70.00")),
        BAssertion(account=sample_accounts[1], date=date(2023, 1, 1), balance=Decimal("-70.00")),
    ]

@pytest.fixture
def journal(sample_accounts, sample_txns, sample_bassertions):
    return Journal(
        accounts=sample_accounts,
        txns=sample_txns,
        bassertions=sample_bassertions
    )

def test_get_accounts_dict(journal: Journal, sample_accounts):
    d = journal.get_accounts_dict()
    assert d["Cash"] == sample_accounts[0]
    assert d["Bank"] == sample_accounts[1]

def test_get_txn_dict(journal: Journal, sample_txns):
    d = journal.get_txn_dict()
    assert d[1] == sample_txns[0]

def test_get_postings(journal: Journal, sample_postings):
    postings = journal.get_postings()
    assert len(postings) == 3
    assert postings[0] == sample_postings[0]
    assert postings[1] == sample_postings[1]
    assert postings[2] == sample_postings[2]

def test_get_account(journal: Journal, sample_accounts):
    assert journal.get_account("Cash") == sample_accounts[0]
    with pytest.raises(ValueError):
        journal.get_account("Nonexistent")

def test_next_txn_id(journal: Journal):
    assert journal.next_txn_id() == 2

def test_known_keys(journal: Journal):
    known = journal.known_keys()
    assert all(isinstance(k, tuple) for k in known.keys())
    assert sum(known.values()) == 3

def test_get_last_balance(journal: Journal, sample_bassertions):
    last = journal.get_last_balance("Cash")
    assert last == sample_bassertions[0]
    assert journal.get_last_balance("Nonexistent") is None

def test_failed_bassertions(journal: Journal):
    # All balances match, so should be empty
    assert journal.failed_bassertions() == []

def test_duplicate_account_name(sample_accounts, sample_txns, sample_bassertions):
    accounts = sample_accounts + sample_accounts[0:1]
    with pytest.raises(ValueError):
        Journal(
            accounts=accounts,
            txns=sample_txns,
            bassertions=sample_bassertions
        )

def test_duplicate_account_number(sample_accounts, sample_txns, sample_bassertions):
    accounts = sample_accounts + [Account(name="Other", number=1000, type="Actifs")]  # type: ignore
    with pytest.raises(ValueError):
        Journal(
            accounts=accounts,
            txns=sample_txns,
            bassertions=sample_bassertions
        )
