from pathlib import Path
from typing import Protocol
from brightsidebudget.journal.journal import Journal
from brightsidebudget.txn.txn import Txn

from brightsidebudget.account.account_repository import (
    ExcelAccountRepository
)
from brightsidebudget.txn.posting_repository import (
    ExcelPostingRepository
)
from brightsidebudget.bassertion.bassertion_repository import (
    ExcelBAssertionRepository
)

class IJournalRepository(Protocol):
    def write_journal(self, *, journal: Journal, destination: Path):
        ...

    def get_journal(self, source: Path) -> Journal:
        ...

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
