import csv
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, Field
from brightsidebudget.account.account import Account
from brightsidebudget.txn.posting import Posting

class BankCsv(BaseModel):
    """
    Class to handle bank CSV imports.
    """
    file: Path
    date_col: str = Field(..., min_length=1)
    account: Account
    stmt_desc_cols: list[str] = []
    stmt_date_col: str = ""
    amount_col: str = ""
    amount_in_col: str = ""
    amount_out_col: str = ""
    encoding: str = "utf8"
    csv_delimiter: str = ","
    remove_delimiter_from: list[str] = []
    skiprows: int = 0

    def get_bank_postings(self, next_txnid: int = 1) -> list[Posting]:
        if self.remove_delimiter_from:
            # Load the file, remove the delimiters and save it back
            with open(self.file, 'r', encoding=self.encoding) as f:
                lines = f.readlines()
            for txn_id, line in enumerate(lines):
                for d in self.remove_delimiter_from:
                    new_d = d.replace(",", "")
                    lines[txn_id] = line.replace(d, new_d)
            with open(self.file, 'w', encoding=self.encoding) as f:
                f.writelines(lines)

        with open(self.file, 'r', encoding=self.encoding) as f:
            for _ in range(self.skiprows):
                next(f)
            reader = csv.DictReader(f, delimiter=self.csv_delimiter)
            ps = []
            for txn_id, row in enumerate(reader, start=next_txnid):
                if self.amount_col:
                    amount = row[self.amount_col]
                else:
                    amount_in = row[self.amount_in_col]
                    if not amount_in:
                        amount_in = "0"
                    amount_out = row[self.amount_out_col]
                    if not amount_out:
                        amount_out = "0"
                    amount = Decimal(amount_in) - Decimal(amount_out)

                if not self.stmt_date_col:
                    stmt_date = None
                else:
                    stmt_date = row[self.stmt_date_col]

                stmt_desc = []
                for col in self.stmt_desc_cols:
                    if row[col]:
                        stmt_desc.append(row[col])
                stmt_desc = " | ".join(stmt_desc)

                ps.append(Posting(txn_id=txn_id, date=row[self.date_col], account=self.account, # type: ignore
                                  amount=amount, comment="", # type: ignore
                                  stmt_date=stmt_date, stmt_desc=stmt_desc)) # type: ignore
            return ps
