import pytest
from datetime import date
from decimal import Decimal
from brightsidebudget.bassertion import BAssertion
from brightsidebudget.account.account import Account

@pytest.fixture
def sample_account():
    return Account(name="Checking", number=1234, type="Actifs") # type: ignore

@pytest.fixture
def sample_bassertion(sample_account):
    return BAssertion(
        date=date(2024, 6, 1),
        account=sample_account,
        balance=Decimal("100.50"),
        comment="Test comment"
    )

def test_dedup_key(sample_bassertion):
    key = sample_bassertion.dedup_key()
    assert key == (date(2024, 6, 1), "Checking")

def test_sort_key(sample_bassertion: BAssertion):
    key = sample_bassertion.sort_key()
    assert key == (date(2024, 6, 1), 1234)

def test_default_comment(sample_account):
    bassertion = BAssertion(
        date=date(2024, 6, 2),
        account=sample_account,
        balance=Decimal("0.00")
    )
    assert bassertion.comment == ""