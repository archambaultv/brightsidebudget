from datetime import date
from decimal import Decimal
from brightsidebudget import BAssertion, QName


def test_bassertion():
    b1 = BAssertion(date=date(2021, 1, 1), acc_qname="A:B:C", balance=Decimal("100.00"))
    b2 = BAssertion(date=date(2021, 1, 1), acc_qname=QName("A:B:C"), balance=Decimal("100.00"))
    assert isinstance(b1.acc_qname, QName)
    assert b1.acc_qname == b2.acc_qname

    # Tags
    b2 = BAssertion(date=date(2021, 1, 1), acc_qname="A:B:C", balance=Decimal("100.00"),
                    tags={"tag1": "value1"})
    assert b2.tags["tag1"] == "value1"
