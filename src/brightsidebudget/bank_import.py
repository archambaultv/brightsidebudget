
import csv
from datetime import date
from decimal import Decimal
from io import StringIO
from typing import Callable, Union
from brightsidebudget.account import QName
from brightsidebudget.journal import Journal
from brightsidebudget.txn import Posting, Txn


# This modules provides the building blocks to import bank transactions from a CSV file

class BankCsv():
    """
    Configuration for importing bank transactions from a CSV file.
    """
    def __init__(self, *, file: str, qname: QName | None, date_col: str,
                 amount_col: str | None = None,
                 amount_in_col: str | None = None,
                 amount_out_col: str | None = None,
                 stmt_desc_cols: Union[list[str], None] = None,
                 stmt_date_col: str | None = None,
                 remove_delimiter_from: str | list[str] | None = None,
                 skiprows: int = 0,
                 dictreader_args: dict[str, str] | None = None,
                 encoding: str = "utf-8"):
        if amount_col is not None and (amount_in_col is not None or amount_out_col is not None):
            raise ValueError("amount_col cannot be used with amount_in_col or amount_out_col.")
        if amount_col is None and (amount_in_col is None or amount_out_col is None):
            raise ValueError("Both amount_in_col and amount_out_col must be set.")

        self.file = file
        self.encoding = encoding
        self.acc_qname = qname if isinstance(qname, QName) else QName(qname)
        self.date_col = date_col
        self.amount_col = amount_col
        self.amount_in_col = amount_in_col
        self.amount_out_col = amount_out_col
        self.stmt_desc_cols = stmt_desc_cols or []
        self.stmt_date_col = stmt_date_col
        if isinstance(remove_delimiter_from, str):
            self.remove_delimiter_from = [remove_delimiter_from]
        else:
            self.remove_delimiter_from = remove_delimiter_from or []
        self.skiprows = skiprows
        self.dictreader_args = dictreader_args or {}

    def import_bank_postings(self, txnid: int = 1) -> list[Posting]:
        """
        Import bank postings from the CSV file.

        Returns a list of Posting objects with extra fields as tags.
        """

        def remove_unquoted_delimiter(content: str) -> str:
            d = self.dictreader_args.get("separator", ",")
            for x in self.remove_delimiter_from:
                content = content.replace(x, x.replace(d, ""))
            return content

        if self.remove_delimiter_from:
            with open(self.file, "r", encoding=self.encoding) as f:
                content = f.read()
            content = remove_unquoted_delimiter(content)
            file = StringIO(content)
        else:
            file = open(self.file, "r", encoding=self.encoding)

        ps = []
        with file as f:
            for _ in range(self.skiprows):
                next(f)
            for row in csv.DictReader(f, **self.dictreader_args):
                dt = date.fromisoformat(row[self.date_col])
                if self.amount_col:
                    amnt = Decimal(row[self.amount_col]) if row[self.amount_col] else Decimal(0)
                else:
                    in_col = row[self.amount_in_col] if row[self.amount_in_col] else "0"
                    out_col = row[self.amount_out_col] if row[self.amount_out_col] else "0"
                    amnt_in = Decimal(in_col)
                    amnt_out = Decimal(out_col)
                    amnt = amnt_in - amnt_out
                stmt_desc = []
                for k in self.stmt_desc_cols:
                    if row[k]:
                        stmt_desc.append(row[k])
                stmt_desc = " | ".join(stmt_desc)
                if self.stmt_date_col:
                    stmt_dt = row[self.stmt_date_col]
                else:
                    stmt_dt = dt
                d = row.copy()
                for x in [self.date_col, self.amount_col, self.amount_in_col, self.amount_out_col,
                          self.stmt_date_col]:
                    if x:
                        d.pop(x, None)
                if len(self.stmt_desc_cols) == 1:
                    d.pop(self.stmt_desc_cols[0], None)
                p = Posting(txnid=txnid, date=dt, acc_qname=self.acc_qname, amount=amnt,
                            stmt_desc=stmt_desc, stmt_date=stmt_dt, tags=d)
                ps.append(p)
                txnid += 1
        return ps


def import_bank_csv(journal: Journal, conf: BankCsv,
                    classifier: Callable[[Posting], Txn | list[Txn] | None],
                    only_after: date | None = None) -> list[Txn]:
    """
    Import bank transactions from a CSV file into the journal. Filters out
    duplicates already in the journal. Returns the list of accepted postings.

    If the conf does not use the full qualified name, it will be converted to
    a full qualified name.

    The classifier function should take a Posting object and return a list of Txn
    objects that represent the transactions to be added to the journal. If the
    Txn object is not accepted, the classifier should return None.
    """
    # Use full qualified name
    conf.acc_qname = journal.chartOfAccounts.full_qname(conf.acc_qname)

    # import bank csv
    bank_ps: list[Posting] = conf.import_bank_postings(txnid=journal.next_txn_id)

    # Build deduplication dictionary
    dedup_ps: list[Posting] = []
    for p in journal.postings:
        if p.acc_qname == conf.acc_qname or p.acc_qname.is_descendant_of(conf.acc_qname):
            dedup_ps.append(p)

    dedup_dict = {}
    for p in dedup_ps:
        key = p.date, p.amount, p.stmt_desc
        if key not in dedup_dict:
            dedup_dict[key] = 0
        dedup_dict[key] += 1

    # Filter out duplicates
    new_ps: list[Posting] = []
    for p in bank_ps:
        if only_after and p.date <= only_after:
            continue
        key = p.date, p.amount, p.stmt_desc
        if key in dedup_dict:
            dedup_dict[key] -= 1
            if dedup_dict[key] == 0:
                dedup_dict.pop(key)
        else:
            new_ps.append(p)

    # Classify and add txns
    accepted_txns: list[Txn] = []
    for p in new_ps:
        ts = classifier(p)
        if isinstance(ts, Txn):
            ts = [ts]
        if ts:
            accepted_txns.extend(ts)
    journal.add_txns(accepted_txns)

    return accepted_txns
