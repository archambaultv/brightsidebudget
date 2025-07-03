from pathlib import Path
from typing import Protocol
from brightsidebudget.journal.journal import Journal
from brightsidebudget.txn.txn import Txn

from brightsidebudget.account.account_repository import (
    CsvAccountRepository, ExcelAccountRepository
)
from brightsidebudget.txn.posting_repository import (
    CsvPostingRepository, ExcelPostingRepository
)
from brightsidebudget.bassertion.bassertion_repository import (
    CsvBAssertionRepository, ExcelBAssertionRepository
)

class IJournalRepository(Protocol):
    def write_journal(self, *, journal: Journal, destination: Path):
        ...

    def get_journal(self, source: Path) -> Journal:
        ...

class CsvJournalRepository(IJournalRepository):
    """
    Journal repository for CSV files.
    Expects three files in the destination directory:
      - Comptes.csv
      - Transactions.csv
      - Soldes.csv
    """
    def write_journal(self, *, journal: Journal, destination: Path):
        dest = Path(destination)
        dest.mkdir(parents=True, exist_ok=True)
        CsvAccountRepository().write_accounts(
            accounts=journal.accounts,
            destination=dest / "Comptes.csv"
        )
        CsvPostingRepository().write_postings(
            postings=journal.get_postings(),
            destination=dest / "Transactions.csv"
        )
        CsvBAssertionRepository().write_bassertions(
            bassertions=journal.bassertions,
            destination=dest / "Soldes.csv"
        )

    def get_journal(self, source: Path) -> Journal:
        src = Path(source)
        accounts = CsvAccountRepository().get_accounts(src / "Comptes.csv")
        accounts_dict = {a.name: a for a in accounts}
        postings = CsvPostingRepository().get_postings(src / "Transactions.csv", accounts_dict)
        txns = Txn.from_postings(postings)
        bassertions = CsvBAssertionRepository().get_bassertions(src / "Soldes.csv", accounts_dict)
        return Journal(accounts=accounts, txns=txns, bassertions=bassertions)

class ExcelJournalRepository(IJournalRepository):
    """
    Journal repository for Excel files.
    Expects a single workbook with three sheets:
      - Comptes
      - Txns
      - Soldes
    """
    def write_journal(self, *, journal: Journal, destination: Path):
        dest = Path(destination)
        # Write all three sheets to the same workbook
        wb_path = dest
        ExcelAccountRepository().write_accounts(
            accounts=journal.accounts,
            destination=wb_path
        )
        ExcelPostingRepository().write_postings(
            postings=journal.get_postings(),
            destination=wb_path
        )
        ExcelBAssertionRepository().write_bassertions(
            bassertions=journal.bassertions,
            destination=wb_path
        )

    def get_journal(self, source: Path) -> Journal:
        src = Path(source)
        accounts = ExcelAccountRepository().get_accounts(src)
        accounts_dict = {a.name: a for a in accounts}
        postings = ExcelPostingRepository().get_postings(src, accounts_dict)
        txns = Txn.from_postings(postings)
        bassertions = ExcelBAssertionRepository().get_bassertions(src, accounts_dict)
        return Journal(accounts=accounts, txns=txns, bassertions=bassertions)
