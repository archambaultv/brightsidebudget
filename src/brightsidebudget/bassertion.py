import csv
from datetime import date
from decimal import Decimal
from typing import Union
from brightsidebudget.account import QName, clean_tags
from brightsidebudget.i18n import BAssertionHeader


class BAssertion():
    """
    A BAssertion (Balance Assertion) is a statement that a certain account
    should have a specific balance at a certain date.
    """
    def __init__(self, *, date: date, acc_qname: Union[QName, str], balance: Decimal,
                 tags: Union[dict[str, str], None] = None):
        self.date = date
        self._acc_qname = acc_qname if isinstance(acc_qname, QName) else QName(acc_qname)
        self.balance = balance
        self.tags = tags or {}

    @property
    def acc_qname(self) -> QName:
        return self._acc_qname

    @acc_qname.setter
    def acc_qname(self, value: Union[QName, str]):
        if isinstance(value, QName):
            self._acc_qname = value
        else:
            self._acc_qname = QName(value)

    def __str__(self):
        return f'BAssertion {self.date} {self.acc_qname} {self.balance}'

    def __repr__(self):
        return self.__str__()

    def tag(self, key: str) -> Union[str, None]:
        return self.tags.get(key, None)

    def copy(self) -> 'BAssertion':
        return BAssertion(date=self.date, acc_qname=self._acc_qname, balance=self.balance,
                          tags=self.tags.copy())


def load_balances(balances: str, encoding: str = "utf8",
                  bassertion_header: Union[BAssertionHeader, None] = None) -> list[BAssertion]:
    """
    Load balance assertions from a CSV file. The file must have a header with the
    date, account name, and balance. The account name is the qualified name of the
    account.
    """
    if bassertion_header is None:
        bassertion_header = BAssertionHeader()
    bs = []
    with open(balances, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = date.fromisoformat(row[bassertion_header.date])
            acc = row[bassertion_header.account]
            balance = Decimal(row[bassertion_header.balance])
            d = row.copy()
            ctx = f"{dt} {acc} {balance}"
            clean_tags(d, forbidden=bassertion_header, err_ctx=ctx)

            bs.append(BAssertion(date=dt, acc_qname=acc, balance=balance, tags=d))
    return bs
