from datetime import date
from decimal import Decimal
from brightsidebudget import Journal


def test_from_csv(accounts_file, txns_file, bassertions_file):
    j = Journal.from_csv(accounts=accounts_file, txns=txns_file, bassertions=bassertions_file)
    assert len(j.accounts) == 17
    assert len(j.postings) == 8
    assert len(j.bassertions) == 6


def test_check_balances(accounts_file, txns_file, bassertions_file):
    j = Journal.from_csv(accounts=accounts_file, txns=txns_file, bassertions=bassertions_file)
    err = j.check_bassertions()
    assert len(err) == 0


def test_txn_extra(accounts_file, txns_file, bassertions_file):
    j = Journal.from_csv(accounts=accounts_file, txns=txns_file, bassertions=bassertions_file)
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
