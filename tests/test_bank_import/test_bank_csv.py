from decimal import Decimal
import pytest
from brightsidebudget.bank_import.bank_csv import BankCsv
from brightsidebudget.account.account import Account
from brightsidebudget.config.import_config import BankCsvConfig

@pytest.fixture
def account():
    return Account(name="Compte chèque", type="Actifs", number=1001) # type: ignore

@pytest.fixture
def bank_csv(account, bank_csv_fixture_path):
    return BankCsv(
        file=bank_csv_fixture_path,
        account=account,
        config=BankCsvConfig(
        date_col="date",
        stmt_desc_cols=["category", "description"],
        amount_in_col="credit",
        amount_out_col="debit",
        encoding="utf8",
        csv_delimiter=",",
        skiprows=0)
    )

def test_get_bank_postings_returns_correct_number(bank_csv: BankCsv):
    postings = bank_csv.get_bank_postings()
    assert len(postings) == 9

def test_posting_fields(bank_csv: BankCsv, account: Account):
    postings = bank_csv.get_bank_postings()
    first = postings[0]
    assert str(first.date) == "2025-02-01"
    assert first.account == account
    assert first.amount == Decimal("2500.00") - Decimal("0.00")
    assert first.stmt_desc == "Salaire | ENTREPRISE QUÉBEC INC"

    second = postings[1]
    assert second.amount == Decimal("0.00") - Decimal("65.80")
    assert "Epicerie" in second.stmt_desc
    assert "METRO PLUS MONTRÉAL" in second.stmt_desc

    # 4th row: credit 350.00, debit 0.00
    assert postings[3].amount == Decimal("350.00") - Decimal("0.00")
    # 5th row: credit 0.00, debit 45.20
    assert postings[4].amount == Decimal("0.00") - Decimal("45.20")

def test_stmt_desc_joins_multiple_columns(bank_csv: BankCsv):
    postings = bank_csv.get_bank_postings()
    for p in postings:
        assert " | " in p.stmt_desc
