import pytest


@pytest.fixture()
def accounts_file() -> str:
    return "tests/fixtures/accounts.csv"


@pytest.fixture()
def bank_checking_file() -> str:
    return "tests/fixtures/bank_checking.csv"


@pytest.fixture()
def bassertions_file() -> str:
    return "tests/fixtures/bassertions.csv"


@pytest.fixture()
def txns_file() -> str:
    return "tests/fixtures/txns.csv"
