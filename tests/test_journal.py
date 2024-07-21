from datetime import date
from brightsidebudget import Journal


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
