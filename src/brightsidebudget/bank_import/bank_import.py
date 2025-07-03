import csv
from decimal import Decimal

from pydantic import BaseModel, Field
from brightsidebudget.account.account import Account
from brightsidebudget.bank_import.classifier import IClassifier
from brightsidebudget.journal.journal import Journal
from brightsidebudget.txn.posting import Posting
from brightsidebudget.txn.txn import Txn

class BankCsv(BaseModel):
    """
    Class to handle bank CSV imports.
    """
    file: str = Field(..., min_length=1)
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


    def get_new_txns(self, journal: Journal, classifier: IClassifier) -> list[Txn]:
        bank_ps = self.get_bank_postings()

        # Remove postings that are already in the database
        last = journal.get_last_balance(self.account)
        known = journal.known_keys()
        new_ps = []
        for p in bank_ps:
            if last is not None and p.date <= last.date:
                continue
            if p.dedup_key() in known:
                known[p.dedup_key()] -= 1
                if known[p.dedup_key()] == 0:
                    del known[p.dedup_key()]
                continue
            new_ps.append(p)

        # Classify the new postings
        new_txns: list[Txn] = []
        for p in new_ps:
            txns = classifier.classify(posting=p)
            if not txns:
                continue
            if isinstance(txns, Txn):
                txns = [txns]
            new_txns.extend(txns)

        # Renumber the transactions
        next_txnid = journal.next_txn_id()
        for i, txn in enumerate(new_txns, start=next_txnid):
            ps = []
            for p in txn.postings:
                # Create a new posting with the same data but a new txn_id
                ps.append(p.model_copy(update={"txn_id": i}))
            new_txns[i - next_txnid] = Txn(postings=ps)

        return new_txns
