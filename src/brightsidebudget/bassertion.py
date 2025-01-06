import csv
from datetime import date
from decimal import Decimal
from pathlib import PosixPath
from typing import Callable, Iterable
from brightsidebudget.account import QName, clean_tags
from brightsidebudget.tag import HasTags, all_tags


class BAssertion(HasTags):
    """
    A BAssertion (Balance Assertion) is a statement that a certain account
    should have a specific balance at a certain date.
    """
    def __init__(self, *, date: date, acc_qname: QName | str, balance: Decimal,
                 tags: dict[str, str] | None = None):
        super().__init__(tags)
        self.date = date
        self.acc_qname = acc_qname if isinstance(acc_qname, QName) else QName(acc_qname)
        self.balance = balance

    def __str__(self):
        return f'BAssertion {self.date} {self.acc_qname} {self.balance}'

    def __repr__(self):
        return self.__str__()

    def copy(self):
        return BAssertion(date=self.date, acc_qname=self.acc_qname, balance=self.balance,
                          tags=self.tags.copy())


def load_balances(balances: str, encoding: str = "utf8") -> list[BAssertion]:
    """
    Load balance assertions from a CSV file. The file must have a header with the
    date, account name, and balance. The account name is the qualified name of the
    account.
    """
    bs = []
    with open(balances, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = date.fromisoformat(row["Date"])
            acc = row["Compte"]
            balance = Decimal(row["Solde"])
            d = row.copy()
            ctx = f"{dt} {acc} {balance}"
            clean_tags(d, forbidden=["Date", "Compte", "Solde"], err_ctx=ctx)

            bs.append(BAssertion(date=dt, acc_qname=acc, balance=balance, tags=d))
    return bs


def write_bassertions(*,
                      bassertions: Iterable[BAssertion],
                      file: str | PosixPath,
                      short_name: Callable[[QName], QName] | None = None,
                      encoding="utf8"):
    """
    Write the balance assertions to a CSV file.
    """
    if short_name is None:
        def short_name(qname: QName) -> QName:
            return qname

    bassertions = sorted(bassertions, key=lambda x: (x.date, x.acc_qname.sort_key))

    with open(file, "w", encoding=encoding) as f:
        writer = csv.writer(f, lineterminator="\n")
        header = ["Date", "Compte", "Solde"]
        b_tag_keys = all_tags(bassertions)
        header += b_tag_keys
        writer.writerow(header)
        for b in bassertions:
            row = [b.date, short_name(b.acc_qname).qstr, b.balance]
            for k in b_tag_keys:
                row.append(b.tags.get(k, ""))
            writer.writerow(row)
