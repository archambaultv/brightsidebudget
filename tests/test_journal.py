from datetime import date
from decimal import Decimal
from brightsidebudget import Journal, BAssertion


def test_from_csv(accounts_file, txns_file, bassertions_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file, bassertions=bassertions_file)
    assert len(j.accounts) == 17
    assert len(j.postings) == 8
    assert len(j.bassertions) == 6


def test_check_balances(accounts_file, txns_file, bassertions_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file, bassertions=bassertions_file)
    err = j.failed_bassertions(today=date(2021, 1, 30))
    assert len(err) == 0


def test_check_balances2(accounts_file, bassertions_file):
    j = Journal.from_csv(accounts=accounts_file, postings=[], bassertions=bassertions_file)
    err = j.failed_bassertions(today=date(2021, 1, 30))
    assert len(err) == 6


def test_next_txn_id(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    assert j.next_txn_id == 3


def test_balance(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    assert j.balance(date(2021, 1, 2), 'Assets:Checking') == Decimal(2460)
    assert j.balance(date(2021, 1, 2), 'Assets:Savings') == Decimal(15000)
    assert j.balance(date(2021, 1, 2), 'Assets:House') == Decimal(450000)
    assert j.balance(date(2021, 1, 2), 'Assets') == Decimal(467460)


def test_adjust_for_bassertion(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    b = BAssertion(date=date(2021, 1, 3), acc_qname='Checking', balance=Decimal(4460))
    t = j.adjust_for_bassertion(b, counterpart='Salary', child=None,
                                comment='Adjustment for bassertion')
    assert t.txnid == 3
    assert t.date == date(2021, 1, 3)
    assert t.postings[0].acc_qname.qstr == 'Assets:Checking'
    assert t.postings[0].amount == Decimal(2000)
    assert t.postings[0].comment == 'Adjustment for bassertion'
    assert t.postings[1].acc_qname.qstr == 'Revenue:Salary'
    assert t.postings[1].amount == Decimal(-2000)
    assert t.postings[1].comment == 'Adjustment for bassertion'
    assert len(j.postings) == 10


def test_adjust_for_bassertion_child(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    b = BAssertion(date=date(2021, 1, 3), acc_qname='Assets', balance=Decimal(467461))
    t = j.adjust_for_bassertion(b, counterpart='Salary', child='Checking',
                                comment='Adjustment for bassertion')
    assert t.txnid == 3
    assert t.date == date(2021, 1, 3)
    assert t.postings[0].acc_qname.qstr == 'Assets:Checking'
    assert t.postings[0].amount == Decimal(1)
    assert t.postings[0].comment == 'Adjustment for bassertion'
    assert t.postings[1].acc_qname.qstr == 'Revenue:Salary'
    assert t.postings[1].amount == Decimal(-1)
    assert t.postings[1].comment == 'Adjustment for bassertion'
    assert len(j.postings) == 10


def test_empty_journal():
    j = Journal()
    assert len(j.accounts) == 0
    assert len(j.postings) == 0
    assert len(j.bassertions) == 0


def test_no_txns(accounts_file):
    j = Journal.from_csv(accounts=accounts_file, postings=[])
    assert len(j.accounts) == 17
    assert len(j.postings) == 0
    assert len(j.bassertions) == 0


def test_no_bassertions(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    assert len(j.accounts) == 17
    assert len(j.postings) == 8
    assert len(j.bassertions) == 0
