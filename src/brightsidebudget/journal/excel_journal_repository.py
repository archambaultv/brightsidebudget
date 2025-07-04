from pathlib import Path

import openpyxl
from brightsidebudget.journal.journal import Journal
from brightsidebudget.txn.txn import Txn

from brightsidebudget.account.excel_account_repository import (
    ExcelAccountRepository
)
from brightsidebudget.txn.posting_repository import (
    ExcelPostingRepository
)
from brightsidebudget.bassertion.excel_bassertion_repository import (
    ExcelBAssertionRepository
)
from brightsidebudget.utils.excel_utils import get_or_create_clean_ws, load_or_create_workbook


class ExcelJournalRepository():
    """
    Journal repository for Excel files.
    Expects a single workbook with three sheets:
      - Comptes
      - Txns
      - Soldes
    """
    def write_journal(self, *, journal: Journal,
                      destination: Path) -> None:
        wb = load_or_create_workbook(destination)

        # Write all three sheets to the same workbook
        ws = get_or_create_clean_ws(wb, "Comptes")
        ExcelAccountRepository().write_accounts_worksheet(
            accounts=journal.accounts,
            ws=ws
        )

        ws = get_or_create_clean_ws(wb, "Txns")
        ExcelPostingRepository().write_postings_worksheet(
            postings=journal.get_postings(),
            ws=ws
        )

        ws = get_or_create_clean_ws(wb, "Soldes")
        ExcelBAssertionRepository().write_bassertions_worksheet(
            bassertions=journal.bassertions,
            ws=ws
        )
        wb.save(destination)

    def get_journal(self, source: Path) -> Journal:
        wb = openpyxl.load_workbook(source, data_only=True)
        accounts = ExcelAccountRepository().get_accounts_worksheet(wb["Comptes"])
        accounts_dict = {a.name: a for a in accounts}
        postings = ExcelPostingRepository().get_postings_worksheet(wb["Txns"], accounts_dict)
        txns = Txn.from_postings(postings)
        bassertions = ExcelBAssertionRepository().get_bassertions_worksheet(wb["Soldes"], accounts_dict)
        return Journal(accounts=accounts, txns=txns, bassertions=bassertions)
