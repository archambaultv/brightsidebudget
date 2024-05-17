from datetime import date
from decimal import Decimal

import pytest
from brightsidebudget import Journal, Posting


def test_from_csv(accounts_file, txns_file, bassertions_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file, bassertions=bassertions_file)
    assert len(j.accounts) == 17
    assert len(j.postings) == 8
    assert len(j.bassertions) == 6


def test_check_balances(accounts_file, txns_file, bassertions_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file, bassertions=bassertions_file)
    err = j.check_bassertions()
    assert len(err) == 0


def test_txn_extra(accounts_file, txns_file, bassertions_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file, bassertions=bassertions_file)
    r = j.postings_extra(today=date(2021, 1, 30))
    assert len(r) == 8
    assert r[0].to_dict() == {"Txn": 1, "Date": date(2021, 1, 1), "Account": "Checking",
                              "Amount": Decimal(2500), 'Account depth': 2, "Description": None,
                              'Fiscal month': 1, 'Fiscal year': 2021, 'Future date': False,
                              'Hierarchy depth 1': 'Assets', 'Hierarchy depth 2': 'Checking',
                              'Hierarchy depth 3': None, 'Last 182 days': True,
                              'Last 30 days': True, 'Last 365 days': True, 'Last 91 days': True,
                              'Month': 1, 'Parent': 'Assets', 'Year': 2021,
                              'Txn accounts': ['Checking', 'Credit card', 'House', 'Mortgage',
                                               'Opening balance', 'Savings']}


def test_next_txn_id(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    next_id = j.next_txn_id()
    assert next_id == 3


def test_txn_extra2(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    ps = j.postings
    next_id = j.next_txn_id()
    ps.append(Posting(txn=next_id, date=date(2021, 2, 1), account="Checking", amount=2500,
                      tags={"Description": None}))
    ps.append(Posting(txn=next_id, date=date(2021, 2, 1), account="Savings", amount=-2500,
                      tags={"Description": None}))
    r = j.postings_extra(ps=ps, today=date(2021, 1, 30))
    assert len(r) == 10
    assert r[-1].to_dict() == {"Txn": 3, "Date": date(2021, 2, 1), "Account": "Savings",
                               "Amount": Decimal(-2500), 'Account depth': 2, "Description": None,
                               'Fiscal month': 2, 'Fiscal year': 2021, 'Future date': True,
                               'Hierarchy depth 1': 'Assets', 'Hierarchy depth 2': 'Savings',
                               'Hierarchy depth 3': None, 'Last 182 days': True,
                               'Last 30 days': True, 'Last 365 days': True, 'Last 91 days': True,
                               'Month': 2, 'Parent': 'Assets', 'Year': 2021,
                               'Txn accounts': ['Checking', 'Savings']}


def test_empty_journal():
    j = Journal(accounts=[], postings=[], bassertions=[])
    assert len(j.accounts) == 0
    assert len(j.postings) == 0
    assert len(j.bassertions) == 0


def test_no_bassertions(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    assert len(j.accounts) == 17
    assert len(j.postings) == 8
    assert isinstance(j.bassertions, list)
    assert len(j.bassertions) == 0


def test_no_txns(accounts_file):
    j = Journal.from_csv(accounts=accounts_file, postings=[])
    assert len(j.accounts) == 17
    assert isinstance(j.postings, list)
    assert len(j.postings) == 0
    assert isinstance(j.bassertions, list)
    assert len(j.bassertions) == 0


@pytest.mark.parametrize("accounts, txns, bas, msg",
                         [([],  # Unknown account
                           [{"Txn": 1, "Date": date(2021, 1, 1), "Account": "A", "Amount": 100}],
                           [],
                           "Unknown account: A",),
                          ([],  # Unknown account
                           [],
                           [{"Date": date(2016, 1, 1), "Account": "A", "Balance": 100}],
                           "Unknown account: A",),
                          ([{"Account": "A"}, {"Account": "A"}],  # Duplicate account
                           [],
                           [],
                           "Duplicate account A"),
                          ([{"Account": "A", "Parent": "A"}],  # Circular reference
                           [],
                           [],
                           "Cycle in accounts: A -> A"),
                          # Circular reference
                          ([{"Account": "A", "Parent": "B"}, {"Account": "B", "Parent": "A"}],
                           [],
                           [],
                           "Cycle in accounts: A -> B -> A"),
                          # Unbalanced transaction
                          ([{"Account": "A", "Parent": None}, {"Account": "B", "Parent": "A"}],
                           [{"Txn": 1, "Date": date(2021, 1, 1), "Account": "A", "Amount": 100},
                            {"Txn": 1, "Date": date(2021, 1, 1), "Account": "B", "Amount": -99}],
                           [],
                           "Txn 1 is not balanced. Sum: 1"),
                          # Duplicate transaction number
                          ([{"Account": "A", "Parent": None}, {"Account": "B", "Parent": "A"}],
                           [{"Txn": 1, "Date": date(2021, 1, 1), "Account": "A", "Amount": 100},
                            {"Txn": 1, "Date": date(2021, 1, 1), "Account": "B", "Amount": -100},
                            {"Txn": 1, "Date": date(2021, 1, 2), "Account": "A", "Amount": 20},
                            {"Txn": 1, "Date": date(2021, 1, 2), "Account": "B", "Amount": -20}],
                           [],
                           "Txn 1 has 2 dates"),
                          # Duplicate bassertion
                          ([{"Account": "A"}],
                           [],
                           [{"Date": date(2016, 1, 1), "Account": "A", "Balance": 100},
                            {"Date": date(2016, 1, 1), "Account": "A", "Balance": 100}],
                           "Duplicate bassertion: 2016-01-01 A"),])
def test_bad_integrity(accounts, txns, bas, msg):
    with pytest.raises(ValueError, match=msg):
        Journal.from_dicts(accounts=accounts, postings=txns, bassertions=bas)
