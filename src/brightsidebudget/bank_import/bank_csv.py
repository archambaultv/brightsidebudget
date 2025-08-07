import csv
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict
from brightsidebudget.account.account import Account
from brightsidebudget.config.import_config import BankCsvConfig
from brightsidebudget.txn.posting import Posting

class BankCsv(BaseModel):
    """
    Class to handle bank CSV imports.
    """
    model_config = ConfigDict(extra="forbid")

    file: Path
    account: Account
    config: BankCsvConfig

    def get_bank_postings(self, next_txnid: int = 1) -> list[Posting]:
        if self.config.remove_delimiter_from:
            # Load the file, remove the delimiters and save it back
            with open(self.file, 'r', encoding=self.config.encoding) as f:
                lines = f.readlines()
            for txn_id, line in enumerate(lines):
                for d in self.config.remove_delimiter_from:
                    new_d = d.replace(",", "")
                    lines[txn_id] = line.replace(d, new_d)
            with open(self.file, 'w', encoding=self.config.encoding) as f:
                f.writelines(lines)

        with open(self.file, 'r', encoding=self.config.encoding) as f:
            for _ in range(self.config.skiprows):
                next(f)
            reader = csv.DictReader(f, delimiter=self.config.csv_delimiter)
            ps = []
            for txn_id, row in enumerate(reader, start=next_txnid):
                try:
                    if self.config.amount_col:
                        amount = row[self.config.amount_col]
                    else:
                        amount_in = row[self.config.amount_in_col]
                        if not amount_in:
                            amount_in = "0"
                        amount_out = row[self.config.amount_out_col]
                        if not amount_out:
                            amount_out = "0"
                        amount = Decimal(amount_in) - Decimal(amount_out)

                    if not self.config.stmt_date_col:
                        stmt_date = None
                    else:
                        stmt_date = row[self.config.stmt_date_col]

                    stmt_desc = []
                    for col in self.config.stmt_desc_cols:
                        if row[col]:
                            stmt_desc.append(row[col])
                    stmt_desc = " | ".join(stmt_desc)

                    ps.append(Posting(txn_id=txn_id, date=row[self.config.date_col], account=self.account, # type: ignore
                                    amount=amount, comment="", # type: ignore
                                    stmt_date=stmt_date, stmt_desc=stmt_desc)) # type: ignore
                except Exception as e:
                    raise ValueError(f"Error in csv '{self.file}' row {row}") from e
            return ps
