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
from brightsidebudget.utils.excel_utils import get_or_create_clean_ws


class ExcelJournalRepository():
    """
    Journal repository for Excel files.
    Expects a single workbook with three sheets:
      - Comptes
      - Txns
      - Soldes
    """
    def write_journal(self, *, journal: Journal,
                      destination: Path,
                      first_fiscal_month: int = 1) -> None:
        #wb = load_or_create_workbook(destination)
        # Simply creates a new one, because modifying existing tables
        # does not work well with openpyxl
        wb = openpyxl.Workbook()
        if wb.active:
            # If the active sheet is not empty, remove it
            wb.remove(wb.active)

        # Write all three sheets to the same workbook
        ws = get_or_create_clean_ws(wb, "Comptes")
        ExcelAccountRepository().write_accounts_worksheet(
            accounts=journal.accounts,
            ws=ws
        )

        ws = get_or_create_clean_ws(wb, "Txns")

        ExcelPostingRepository().write_txns_extra_worksheet(
            txns=journal.txns,
            ws=ws,
            first_fiscal_month=first_fiscal_month
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
