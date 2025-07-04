from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from brightsidebudget.account.account import Account
from brightsidebudget.txn.posting import Posting
from brightsidebudget.utils.excel_utils import get_or_create_clean_ws, load_or_create_workbook, set_table_range

HEADER = ["No txn", "Date", "Compte", "Montant", "Date du relevé", "Commentaire",
          "Description du relevé"]

class ExcelPostingRepository():
    """Repository for managing postings in Excel format."""
    
    def write_postings(self, *, 
                       postings: list[Posting], 
                       destination: Path):
        """Write postings to Excel file."""
        
        # Load existing workbook or create new one
        wb = load_or_create_workbook(destination)
        ws = get_or_create_clean_ws(wb, "Txns")
        self.write_postings_worksheet(postings=postings, ws=ws)
        wb.save(destination)

    def write_postings_worksheet(self, *,
                                 postings: list[Posting],
                                 ws: Worksheet):
        ps = sorted(postings, key=lambda p: p.sort_key())
        # Add data
        ws.append(HEADER)
        for p in ps:
            ws.append([
                str(p.txn_id),
                str(p.date),
                p.account.name,
                str(p.amount),
                str(p.stmt_date),
                p.comment,
                p.stmt_desc
            ])
        
        # Update the table range
        last_row = ws.max_row
        last_col = len(HEADER)
        new_range = f"A1:{get_column_letter(last_col)}{last_row}"
        set_table_range(ws, "Txns", new_range)
    
    def get_postings(self, source: Path, accounts: dict[str, Account]) -> list[Posting]:
        """Retrieve postings from Excel file."""
        wb = openpyxl.load_workbook(source, data_only=True)
        if "Txns" in wb.sheetnames:
            return self.get_postings_worksheet(wb["Txns"], accounts)
        else:
            raise ValueError("Worksheet 'Txns' not found in the workbook.")

    def get_postings_worksheet(self, ws: Worksheet, accounts: dict[str, Account]) -> list[Posting]:
        postings: list[Posting] = []
        # assume header is in row 1
        for row in ws.iter_rows(min_row=2, values_only=True):
            if len(row) < 7:
                raise ValueError("Row does not contain enough columns for Posting data.")
            txn_id, date_str, compte, montant, stmt_date_str, commentaire, description = row
            
            try:
                # Convert to dict format expected by Posting.from_dict
                posting = Posting(
                    txn_id=txn_id, # type: ignore
                    date=date_str,  # type: ignore
                    account=accounts[str(compte)],
                    amount=montant,  # type: ignore
                    stmt_date=stmt_date_str, # type: ignore
                    comment=commentaire if commentaire else "",  # type: ignore
                    stmt_desc=description if description else ""  # type: ignore
                )
            except Exception as e:
                raise ValueError(f"Error processing row {row}") from e
            postings.append(posting)
        return postings
