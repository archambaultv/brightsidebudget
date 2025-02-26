import csv
from datetime import datetime
from decimal import Decimal
from typing import Callable
from brightsidebudget.account import Account
from brightsidebudget.journal import Journal
from brightsidebudget.posting import Posting
from brightsidebudget.txn import Txn


class BankCsv:
    def __init__(self, *, file: str, date_col: str, account: Account, stmt_desc_cols: list[str],
                 stmt_date_col: str = "", amount_col: str = "", amount_in_col: str = "",
                 amount_out_col: str = "", encoding: str = "utf8",
                 remove_delimiter_from: list[str] | None = None,
                 skiprows: int = 0):
        self.file = file
        self.date_col = date_col
        self.account = account
        self.stmt_desc_cols = stmt_desc_cols
        self.stmt_date_col = stmt_date_col
        self.amount_col = amount_col
        self.amount_in_col = amount_in_col
        self.amount_out_col = amount_out_col
        self.encoding = encoding
        self.remove_delimiter_from = remove_delimiter_from or []
        self.skiprows = skiprows

    def get_postings(self, next_txnid: int = 1) -> list[Posting]:
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
            reader = csv.DictReader(f, delimiter=";")
            ps = []
            for txn_id, row in enumerate(reader, start=next_txnid):
                dt = datetime.strptime(row[self.date_col], "%Y-%m-%d").date()

                if self.stmt_date_col:
                    stmt_dt = row.get(self.stmt_date_col, dt)
                    if not stmt_dt:
                        stmt_dt = dt
                    if isinstance(stmt_dt, str):
                        stmt_dt = datetime.strptime(stmt_dt, "%Y-%m-%d").date()
                else:
                    stmt_dt = dt

                if self.amount_col:
                    amount = Decimal(row[self.amount_col])
                else:
                    amount_in = row[self.amount_in_col]
                    if not amount_in:
                        amount_in = "0"
                    amount_out = row[self.amount_out_col]
                    if not amount_out:
                        amount_out = "0"
                    amount = Decimal(amount_in) - Decimal(amount_out)

                stmt_desc = []
                for col in self.stmt_desc_cols:
                    if row[col]:
                        stmt_desc.append(row[col])
                stmt_desc = " | ".join(stmt_desc)

                ps.append(Posting(txn_id=txn_id, date=dt, account=self.account,
                                  amount=amount, comment="",
                                  stmt_date=stmt_dt, stmt_desc=stmt_desc))
            return ps


def import_bank_csv(journal: Journal, bank_csv: BankCsv,
                    classify: Callable[[Posting], Txn | list[Txn] | None]) -> list[Posting]:
    bank_ps = bank_csv.get_postings()

    # Remove postings that are already in the database
    last = journal.get_last_balance(bank_csv.account)
    known = journal.known_keys()

    new_ps = []
    for p in bank_ps:
        if p.dedup_key() in known:
            known[p.dedup_key()] -= 1
            if known[p.dedup_key()] == 0:
                del known[p.dedup_key()]
            continue
        if last is not None and p.date <= last.date:
            continue
        new_ps.append(p)

    # Classify the new postings
    ok_ps = []
    next_txn_id = journal.next_txn_id()
    for p in new_ps:
        new_txns = classify(p)
        if not new_txns:
            continue
        if isinstance(new_txns, Txn):
            new_txns = [new_txns]
        for t in new_txns:
            for p in t:
                p.txn_id = next_txn_id
            next_txn_id += 1
        ok_ps.extend(new_txns)

    return ok_ps
