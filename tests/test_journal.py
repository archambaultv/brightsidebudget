from datetime import date
from decimal import Decimal

import pytest
from brightsidebudget import Journal, BAssertion, Account, AccountHeader, TxnHeader, \
    BAssertionHeader, TargetHeader


def test_from_csv(accounts_file, txns_file, bassertions_file, budget_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file,
                         bassertions=bassertions_file, targets=budget_file)
    verify_from_csv(j)


def verify_from_csv(j: Journal):
    assert len(j.accounts) == 17
    assert len(j.postings) == 8
    assert len(j.bassertions) == 6
    assert len(j.targets) == 4
    a = j.account('Assets:Checking')
    assert "Tag 1" not in a.tags
    a2 = j.account('Assets')
    assert "Tag 1" in a2.tags
    assert len(j.txns_dict) == 2
    txn2 = j.txns_dict[2]
    assert txn2.postings[0].stmt_desc == 'Super market'
    for a in j.accounts:
        assert len(a.tags) in [1, 2]


def test_from_csv_i18n(accounts_file, txns_file, bassertions_file, budget_file,
                       tmp_path):
    # Change the header to a non-English language and use StringIO
    with open(accounts_file, 'r') as f:
        content = f.read()
    content = content.replace('Account', 'Compte')
    accounts_file = tmp_path / 'accounts.csv'
    with open(accounts_file, 'w') as f:
        f.write(content)

    with open(txns_file, 'r') as f:
        content = f.read()
    content = content.replace('Txn,Date,Account,Amount,Statement description',
                              'Txn2,Date2,Compte,Montant,Description du relevé')
    txns_file = tmp_path / 'txns.csv'
    with open(txns_file, 'w') as f:
        f.write(content)

    with open(bassertions_file, 'r') as f:
        content = f.read()
    content = content.replace('Date,Account,Balance',
                              'Date2,Compte,Solde')
    bassertions_file = tmp_path / 'bassertions.csv'
    with open(bassertions_file, 'w') as f:
        f.write(content)

    with open(budget_file, 'r') as f:
        content = f.read()
    content = content.replace('Start date,Account,Amount,Comment,Frequency,Interval,Count,Until',
                              'Début,Compte,Montant,Commentaire,Fréquence,Intervalle,Compter,Fin')
    budget_file = tmp_path / 'budget.csv'
    with open(budget_file, 'w') as f:
        f.write(content)

    acc_header = AccountHeader(account='Compte')
    txn_header = TxnHeader(account='Compte', date='Date2', amount='Montant', txn='Txn2',
                           stmt_desc='Description du relevé')
    bassertion_header = BAssertionHeader(account='Compte', date='Date2', balance='Solde')
    target_header = TargetHeader(account='Compte', start_date='Début', amount='Montant',
                                 comment='Commentaire', frequency='Fréquence',
                                 interval='Intervalle',
                                 count='Compter', until='Fin')
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file,
                         bassertions=bassertions_file, targets=budget_file,
                         acc_header=acc_header, txn_header=txn_header,
                         bassertion_header=bassertion_header, target_header=target_header)
    verify_from_csv(j)


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


def test_short_qnames_1(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    assert j.short_qname('Assets:Checking').qstr == 'Checking'
    assert j.short_qname('Checking').qstr == 'Checking'
    assert j.short_qname('Assets').qstr == 'Assets'
    assert j.short_qname('Expenses:Other').qstr == 'Other'
    assert j.short_qname('Expenses:Food').qstr == 'Food'

    assert j.short_qname('Assets:Checking', min_length=2).qstr == 'Assets:Checking'
    assert j.short_qname('Checking', min_length=2).qstr == 'Assets:Checking'
    assert j.short_qname('Assets', min_length=2).qstr == 'Assets'


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


def test_to_polars(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    df = j.to_polars()

    assert len(df) == 8
    expected_cols = ['Txn', 'Date', 'Account',  'Account short name',
                     'Account 1', 'Account 2', 'Account 3', 'Amount', 'Comment',
                     'Stmt date', 'Stmt description', 'Number', 'Tag 1']
    assert len(df.columns) == len(expected_cols)
    for x in expected_cols:
        assert x in df.columns


def test_conflicting_tags(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    ps = []
    for p in j.postings:
        p.tags['Tag 1'] = 'Conflict'
        p.tags['Tag 1_acc'] = 'Conflict again'
        ps.append(p)
    df = j.to_polars(ps)

    assert df['Tag 1'].unique().to_list() == ['Conflict']
    assert df['Tag 1_acc'].unique().to_list() == ['Conflict again']
    assert "Tag 1_acc2" in df.columns


def test_short_qnames_2():
    j = Journal()
    j.add_accounts([Account(qname='Assets'),
                    Account(qname='Assets:Checking'),
                    Account(qname='Assets:Checking:Foo'),
                    Account(qname='Assets:Savings'),
                    Account(qname='Assets:Savings:Foo')])
    assert j.short_qname('Assets:Checking:Foo').qstr == 'Checking:Foo'
    assert j.short_qname('Checking:Foo').qstr == 'Checking:Foo'
    assert j.short_qname('Assets:Savings:Foo').qstr == 'Savings:Foo'
    assert j.short_qname('Savings:Foo').qstr == 'Savings:Foo'

    with pytest.raises(ValueError):
        j.short_qname('Foo')

    # A previous bug appeared only when there was an uneven number of the same
    # account basenames.
    j.add_accounts([Account(qname='Assets:House'),
                    Account(qname='Assets:House:Foo')])

    assert j.short_qname('Assets:Checking:Foo').qstr == 'Checking:Foo'
    assert j.short_qname('Checking:Foo').qstr == 'Checking:Foo'
    assert j.short_qname('Assets:Savings:Foo').qstr == 'Savings:Foo'
    assert j.short_qname('Savings:Foo').qstr == 'Savings:Foo'
    assert j.short_qname('Assets:House:Foo').qstr == 'House:Foo'
    assert j.short_qname('House:Foo').qstr == 'House:Foo'

    with pytest.raises(ValueError):
        j.short_qname('Foo')

    # Now Checking:Foo hides Assets:Checking:Foo
    j.add_accounts([Account(qname='Checking'),
                    Account(qname='Checking:Foo')])

    assert j.short_qname('Assets:Checking:Foo').qstr == 'Assets:Checking:Foo'
    assert j.short_qname('Checking:Foo').qstr == 'Checking:Foo'
    assert j.full_qname('Checking:Foo').qstr == 'Checking:Foo'
    assert j.account('Checking:Foo').qname.qstr == 'Checking:Foo'


def test_duplicate_balance():
    j = Journal()
    j.add_accounts([Account(qname='Assets')])
    j.add_bassertions([BAssertion(date=date(2021, 1, 1), acc_qname='Assets', balance=Decimal(100))])
    with pytest.raises(ValueError):
        j.add_bassertions([BAssertion(date=date(2021, 1, 1), acc_qname='Assets',
                                      balance=Decimal(100))])

    j.add_accounts([Account(qname='Assets:Checking')])
    j.add_bassertions([BAssertion(date=date(2021, 1, 1), acc_qname='Assets:Checking',
                                  balance=Decimal(100))])
    with pytest.raises(ValueError):
        j.add_bassertions([BAssertion(date=date(2021, 1, 1), acc_qname='Checking',
                                      balance=Decimal(100))])
