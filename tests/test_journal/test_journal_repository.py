from decimal import Decimal
from pathlib import Path

from brightsidebudget.account.account import Account
from brightsidebudget.journal.excel_journal_repository import ExcelJournalRepository
from brightsidebudget.journal.journal import Journal
from brightsidebudget.txn.posting import Posting


def test_read_excel(journal_fixture_path):
    excel_repo = ExcelJournalRepository()
    accounts = excel_repo.read_journal(journal_fixture_path)
    _check_journal(accounts)

def _check_journal(journal: Journal):
    _check_accounts(journal.accounts)
    _check_postings(journal.get_postings())


def _check_postings(postings: list[Posting]):
    # Verify we got the expected number of accounts
    assert len(postings) == 4
    
    # Verify specific accounts exist with correct properties
    ps1 = postings[0]
    assert ps1.txn_id == 1
    assert ps1.date.isoformat() == "2025-01-01"
    assert ps1.account.name == "Compte chèque"
    assert ps1.amount == Decimal(2000)
    assert ps1.comment == "Commentaire 1"
    assert ps1.stmt_date.isoformat() == "2025-01-01"
    assert ps1.stmt_desc == "ACME Corp"

    ps2 = postings[1]
    assert ps2.txn_id == 1
    assert ps2.date.isoformat() == "2025-01-01"
    assert ps2.account.name == "Revenus A"
    assert ps2.amount == Decimal(-2000)
    assert ps2.comment == "Commentaire 2"
    assert ps2.stmt_date.isoformat() == "2025-01-01"
    assert ps2.stmt_desc == "ACME Corp"

    ps3 = postings[2]
    assert ps3.txn_id == 2
    assert ps3.date.isoformat() == "2025-01-02"
    assert ps3.account.name == "Compte chèque"
    assert ps3.amount == Decimal("-500.1")
    assert ps3.comment == ""
    assert ps3.stmt_date.isoformat() == "2025-01-02"
    assert ps3.stmt_desc == "Paiement credit"

    ps4 = postings[3]
    assert ps4.txn_id == 2
    assert ps4.date.isoformat() == "2025-01-02"
    assert ps4.account.name == "Hypothèque"
    assert ps4.amount == Decimal("500.1")
    assert ps4.comment == ""
    assert ps4.stmt_date.isoformat() == "2025-01-02"
    assert ps4.stmt_desc == "Paiement credit"

def _check_accounts(accounts: list[Account]):
    # Verify we got the expected number of accounts
    assert len(accounts) == 12
    
    # Verify specific accounts exist with correct properties
    account_names = [acc.name for acc in accounts]
    assert "Compte chèque" in account_names
    assert "REER A" in account_names
    assert "REER B" in account_names
    assert "Carte de crédit" in account_names
    assert "Hypothèque" in account_names
    assert "Soldes d'ouverture" in account_names
    assert "Revenus A" in account_names
    assert "Revenus B" in account_names
    assert "Gain en capital" in account_names
    assert "Dépenses courantes" in account_names
    assert "Intérêts" in account_names
    assert "Non classé" in account_names

    # Test specific account details
    compte_cheque = next(acc for acc in accounts if acc.name == "Compte chèque")
    assert compte_cheque.type.name == "Actifs"
    assert compte_cheque.number == 1001
    assert compte_cheque.group == ""
    assert compte_cheque.subgroup == ""

    reer_a = next(acc for acc in accounts if acc.name == "REER A")
    assert reer_a.type.name == "Actifs"
    assert reer_a.number == 1051
    assert reer_a.group == "Retraite"
    assert reer_a.subgroup == ""

    carte_credit = next(acc for acc in accounts if acc.name == "Carte de crédit")
    assert carte_credit.type.name == "Passifs"
    assert carte_credit.number == 2001
    assert carte_credit.group == ""
    assert carte_credit.subgroup == ""

def test_write_new_excel(journal_fixture_path: Path, output_dir: Path):
    destination = output_dir / f"{journal_fixture_path.stem}-new.xlsx"
    repo = ExcelJournalRepository()
    journal = repo.read_journal(journal_fixture_path)
    repo.write_journal(journal=journal, destination=destination)

    journal2 = repo.read_journal(destination)
    assert journal2 == journal
