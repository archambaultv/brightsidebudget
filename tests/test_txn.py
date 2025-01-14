from datetime import date
from decimal import Decimal
import pytest
from brightsidebudget import Posting, QName, Txn, RPosting


def test_posting():
    p1 = Posting(txnid=1, date=date(2021, 1, 1), acc_qname="A:B:C", amount=Decimal("100.00"))
    p2 = Posting(txnid=1, date=date(2021, 1, 1), acc_qname=QName("A:B:C"),
                 amount=Decimal("100.00"))
    assert isinstance(p1.acc_qname, QName)
    assert p1.acc_qname == p2.acc_qname


def test_txn():
    p1 = Posting(txnid=1, date=date(2021, 1, 1), acc_qname="A:A1", amount=Decimal("100.00"))
    p2 = Posting(txnid=1, date=date(2021, 1, 1), acc_qname=QName("E:E1"),
                 amount=Decimal("-100.00"))
    t = Txn([p1, p2])
    assert t.date == date(2021, 1, 1)
    assert t.txnid == 1

    with pytest.raises(ValueError):
        Txn([])

    with pytest.raises(ValueError):
        Txn([p1])

    p2.amount = Decimal("-99.99")
    with pytest.raises(ValueError):
        Txn([p1, p2])
    p2.amount = Decimal("-100.00")

    p2.txnid = 2
    with pytest.raises(ValueError):
        Txn([p1, p2])
    p2.txnid = 1

    p2.date = date(2021, 1, 2)
    with pytest.raises(ValueError):
        Txn([p1, p2])


def test_rposting():
    r1 = RPosting(start=date(2021, 1, 1), acc_qname="A:B:C", amount=Decimal("100.00"))
    r2 = RPosting(start=date(2021, 1, 1), acc_qname=QName("A:B:C"), amount=Decimal("100.00"))
    assert isinstance(r1.acc_qname, QName)
    assert r1.acc_qname == r2.acc_qname

    ps = r1.postings_between(date(2021, 1, 1), date(2021, 1, 31))
    assert len(ps) == 1
    assert ps[0].date == date(2021, 1, 1)
    assert ps[0].acc_qname == QName("A:B:C")
    assert ps[0].amount == Decimal("100.00")

    ps = r1.postings_between(date(2021, 1, 2), date(2021, 1, 31))
    assert len(ps) == 0

    ps = r1.postings_between(date(2020, 1, 1), date(2020, 12, 31))
    assert len(ps) == 0

    r3 = RPosting(start=date(2021, 1, 1), acc_qname="A:B:C", amount=Decimal("100.00"),
                  frequency="quotidien", interval=2, count=3)
    ps = r3.postings_between(date(2021, 1, 1), date(2021, 1, 31))
    assert len(ps) == 3
    assert ps[0].date == date(2021, 1, 1)
    assert ps[1].date == date(2021, 1, 3)
    assert ps[2].date == date(2021, 1, 5)

    r4 = RPosting(start=date(2021, 1, 1), acc_qname="A:B:C", amount=Decimal("100.00"),
                  frequency="mensuel", interval=2, until=date(2021, 6, 1))
    ps = r4.postings_between(date(2021, 1, 1), date(2021, 6, 1))
    assert len(ps) == 3
    assert ps[0].date == date(2021, 1, 1)
    assert ps[1].date == date(2021, 3, 1)
    assert ps[2].date == date(2021, 5, 1)
