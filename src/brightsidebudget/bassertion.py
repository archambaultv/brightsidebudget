from datetime import date
from decimal import Decimal
from typing import Union
from brightsidebudget.account import QName


class BAssertion():
    """
    A BAssertion (Balance Assertion) is a statement that a certain account
    should have a specific balance at a certain date.
    """
    def __init__(self, *, date: date, acc_qname: Union[QName, str], balance: Decimal):
        self.date = date
        self._acc_qname = acc_qname if isinstance(acc_qname, QName) else QName(acc_qname)
        self.balance = balance

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

    def copy(self) -> 'BAssertion':
        return BAssertion(date=self.date, acc_qname=self._acc_qname, balance=self.balance)
