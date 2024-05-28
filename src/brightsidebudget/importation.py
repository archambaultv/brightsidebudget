import csv
from decimal import Decimal
from io import StringIO
from typing import Callable, Union
from brightsidebudget.journal import Journal, Posting


def read_bank_csv(file: str, account: str, date_col: str,
                  amount_col: Union[str, None] = None,
                  amount_in_col: Union[str, None] = None,
                  amount_out_col: Union[str, None] = None,
                  remove_delimiter_from: Union[str, list[str]] = None,
                  encoding: str = "utf-8",
                  skiprows: int = 0,
                  **dictreader_args) -> list[Posting]:
    # Check amount_col is not set with amount_in_col or amount_out_col
    if amount_col is not None and (amount_in_col is not None or amount_out_col is not None):
        raise ValueError("amount_col cannot be used with amount_in_col or amount_out_col.")
    if amount_col is None and (amount_in_col is None or amount_out_col is None):
        raise ValueError("Both amount_in_col and amount_out_col must be set.")
    if isinstance(remove_delimiter_from, str):
        remove_delimiter_from = [remove_delimiter_from]

    def remove_unquoted_delimiter(content: str) -> str:
        d = dictreader_args.get("separator", ",")
        for x in remove_delimiter_from:
            content = content.replace(x, x.replace(d, ""))
        return content

    if remove_delimiter_from:
        with open(file, "r", encoding=encoding) as f:
            content = f.read()
        content = remove_unquoted_delimiter(content)
        file = StringIO(content)
    else:
        file = open(file, "r", encoding=encoding)

    ps = []
    with file as f:
        for _ in range(skiprows):
            next(f)
        for i, row in enumerate(csv.DictReader(f, **dictreader_args), start=1):
            dt = row[date_col]
            if amount_col:
                amnt = row[amount_col] if row[amount_col] else "0"
            else:
                in_col = row[amount_in_col] if row[amount_in_col] else "0"
                out_col = row[amount_out_col] if row[amount_out_col] else "0"
                amnt_in = Decimal(in_col)
                amnt_out = Decimal(out_col)
                amnt = amnt_in - amnt_out
            for k in [date_col, amount_col, amount_in_col, amount_out_col]:
                if k in row:
                    del row[k]
            p = Posting(txn=i, account=account, date=dt, amount=amnt, tags=row)
            ps.append(p)
    return ps


def remove_duplicates(bank_csv: list[Posting],
                      journal: Journal,
                      fingerprint_tags: list[str] = None) -> list[Posting]:

    # We need to make sure we don't remove
    # more rows than necessary. Ex: if 3 rows in bank_csv have the same fingerprint
    # and only 2 are in the journal, we should remove only 2.
    new = []
    fingerprints = journal.fingerprints(fingerprint_tags)
    for p in bank_csv:
        k = p.fingerprint(fingerprint_tags)
        if k in fingerprints:
            fingerprints[k] -= 1
            if fingerprints[k] == 0:
                del fingerprints[k]
        else:
            new.append(p)

    return new


def balance_posting(bank_csv: list[Posting],
                    balancing: Callable[[Posting], list[tuple[str, Decimal]]],
                    flat: bool = False) -> Union[list[list[Posting]], list[Posting]]:
    txns = []
    for p in bank_csv:
        other_accounts = balancing(p)
        if not other_accounts:
            txns.append([])
            continue
        total = sum(x[1] for x in other_accounts)
        if total != -p.amount:
            raise Exception(f"Balancing failed for {p}. Total: {total}")

        ps = [p]
        for acc, amount in other_accounts:
            p2 = p.copy()
            p2["Account"] = acc
            p2["Amount"] = amount
            ps.append(p2)

        txns.append(ps)
    if flat:
        return [p for ps in txns for p in ps]
    else:
        return txns
