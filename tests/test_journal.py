from datetime import date
from decimal import Decimal

from brightsidebudget.account import QName
from brightsidebudget.tag import all_tags
import pytest
from brightsidebudget import Journal, BAssertion, Account


def test_from_csv(accounts_file, txns_file, bassertions_file, budget_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file,
                         bassertions=bassertions_file, targets=budget_file)
    verify_from_csv(j)


def verify_from_csv(j: Journal):
    assert len(list(j.chartOfAccounts.accounts)) == 18
    assert len(list(j.postings)) == 8
    assert len(j.bassertions_dict) == 6
    assert len(j.budget.rpostings) == 4
    a = j.chartOfAccounts.account('Actifs:Chèque')
    assert "Tag 1" not in a.tags
    a2 = j.chartOfAccounts.account('Actifs')
    assert "Tag 1" in a2.tags
    assert len(j.txns_dict) == 2
    txn2 = j.txns_dict[2]
    assert txn2.postings[0].stmt_desc == 'Super market'
    for a in j.chartOfAccounts.accounts:
        assert len(a.tags) in [1, 2]
    b_tags = all_tags(j.bassertions)
    assert b_tags == ["Commentaire"]
    m = j.bassertions_dict[QName("Actifs:Maison")][date(2021, 1, 1)]
    assert (m.tags["Commentaire"] == "It is a nice house")
    m = j.bassertions_dict[QName("Actifs:Épargne")][date(2021, 1, 1)]
    assert m.tags.get("Commentaire") is None


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

    j = Journal.from_csv(accounts=accounts_file, postings=txns_file,
                         bassertions=bassertions_file, targets=budget_file)
    verify_from_csv(j)


def test_check_balances(accounts_file, txns_file, bassertions_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file, bassertions=bassertions_file)
    err = j.failed_bassertions()
    assert len(err) == 0


def test_check_balances2(accounts_file, bassertions_file):
    j = Journal.from_csv(accounts=accounts_file, postings=[], bassertions=bassertions_file)
    err = j.failed_bassertions()
    assert len(err) == 6


def test_next_txn_id(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    assert j.next_txn_id == 3


def test_balance(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    assert j.balance(date(2021, 1, 2), 'Actifs:Chèque') == Decimal(2460)
    assert j.balance(date(2021, 1, 2), 'Actifs:Épargne') == Decimal(15000)
    assert j.balance(date(2021, 1, 2), 'Actifs:Maison') == Decimal(450000)
    assert j.balance(date(2021, 1, 2), 'Actifs') == Decimal(467460)


def test_adjust_for_bassertions(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    b = BAssertion(date=date(2021, 1, 3), acc_qname='Chèque', balance=Decimal(4460))
    j.add_bassertions(b)
    t = j.adjust_for_bassertions(accounts=['Chèque'], counterparts=['Salaire'],
                                 children=None,
                                 comment='Adjustment for bassertion')
    assert t[0].txnid == 3
    assert t[0].date == date(2021, 1, 3)
    assert t[0].postings[0].acc_qname.qstr == 'Actifs:Chèque'
    assert t[0].postings[0].amount == Decimal(2000)
    assert t[0].postings[0].comment == 'Adjustment for bassertion'
    assert t[0].postings[1].acc_qname.qstr == 'Revenus:Salaire'
    assert t[0].postings[1].amount == Decimal(-2000)
    assert t[0].postings[1].comment == 'Adjustment for bassertion'
    assert len(list(j.postings)) == 10

    b = BAssertion(date=date(2021, 1, 2), acc_qname='Chèque', balance=Decimal(4458))
    j.add_bassertions(b)
    t = j.adjust_for_bassertions(accounts=['Chèque'], counterparts=['Salaire'],
                                 comment='Adjustment for bassertion')
    assert len(t) == 2
    assert len(j.failed_bassertions()) == 0


def test_adjust_for_bassertion_child(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    b = BAssertion(date=date(2021, 1, 3), acc_qname='Actifs', balance=Decimal(467461))
    j.add_bassertions(b)
    t = j.adjust_for_bassertions(accounts=['Actifs'], counterparts=['Salaire'],
                                 children=['Chèque'],
                                 comment='Adjustment for bassertion')

    assert t[0].txnid == 3
    assert t[0].date == date(2021, 1, 3)
    assert t[0].postings[0].acc_qname.qstr == 'Actifs:Chèque'
    assert t[0].postings[0].amount == Decimal(1)
    assert t[0].postings[0].comment == 'Adjustment for bassertion'
    assert t[0].postings[1].acc_qname.qstr == 'Revenus:Salaire'
    assert t[0].postings[1].amount == Decimal(-1)
    assert t[0].postings[1].comment == 'Adjustment for bassertion'
    assert len(list(j.postings)) == 10


def test_short_qnames_1(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    assert j.chartOfAccounts.short_qname('Actifs:Chèque').qstr == 'Chèque'
    assert j.chartOfAccounts.short_qname('Chèque').qstr == 'Chèque'
    assert j.chartOfAccounts.short_qname('Actifs').qstr == 'Actifs'
    assert j.chartOfAccounts.short_qname('Dépenses:Autres').qstr == 'Autres'
    assert j.chartOfAccounts.short_qname('Dépenses:Nourriture').qstr == 'Nourriture'

    j.chartOfAccounts.short_qname_min_length = lambda x: 2 if x.qstr in ['Actifs:Chèque'] else 1
    assert j.chartOfAccounts.short_qname('Actifs:Chèque').qstr == 'Actifs:Chèque'
    assert j.chartOfAccounts.short_qname('Chèque').qstr == 'Actifs:Chèque'
    assert j.chartOfAccounts.short_qname('Actifs').qstr == 'Actifs'


def test_empty_journal():
    j = Journal()
    assert len(list(j.chartOfAccounts.accounts)) == 0
    assert len(list(j.postings)) == 0
    assert len(j.bassertions_dict) == 0


def test_no_txns(accounts_file):
    j = Journal.from_csv(accounts=accounts_file, postings=[])
    assert len(list(j.chartOfAccounts.accounts)) == 18
    assert len(list(j.postings)) == 0
    assert len(j.bassertions_dict) == 0


def test_no_bassertions(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    assert len(list(j.chartOfAccounts.accounts)) == 18
    assert len(list(j.postings)) == 8
    assert len(j.bassertions_dict) == 0


def test_short_qnames_2():
    j = Journal()
    j.add_accounts([Account(qname='Actifs'),
                    Account(qname='Actifs:Chèque'),
                    Account(qname='Actifs:Chèque:Foo'),
                    Account(qname='Actifs:Épargne'),
                    Account(qname='Actifs:Épargne:Foo')])
    assert j.chartOfAccounts.short_qname('Actifs:Chèque:Foo').qstr == 'Chèque:Foo'
    assert j.chartOfAccounts.short_qname('Chèque:Foo').qstr == 'Chèque:Foo'
    assert j.chartOfAccounts.short_qname('Actifs:Épargne:Foo').qstr == 'Épargne:Foo'
    assert j.chartOfAccounts.short_qname('Épargne:Foo').qstr == 'Épargne:Foo'

    with pytest.raises(ValueError):
        j.chartOfAccounts.short_qname('Foo')

    # A previous bug appeared only when there was an uneven number of the same
    # account basenames.
    j.add_accounts([Account(qname='Actifs:Maison'),
                    Account(qname='Actifs:Maison:Foo')])

    assert j.chartOfAccounts.short_qname('Actifs:Chèque:Foo').qstr == 'Chèque:Foo'
    assert j.chartOfAccounts.short_qname('Chèque:Foo').qstr == 'Chèque:Foo'
    assert j.chartOfAccounts.short_qname('Actifs:Épargne:Foo').qstr == 'Épargne:Foo'
    assert j.chartOfAccounts.short_qname('Épargne:Foo').qstr == 'Épargne:Foo'
    assert j.chartOfAccounts.short_qname('Actifs:Maison:Foo').qstr == 'Maison:Foo'
    assert j.chartOfAccounts.short_qname('Maison:Foo').qstr == 'Maison:Foo'

    with pytest.raises(ValueError):
        j.chartOfAccounts.short_qname('Foo')

    # Now Chèque:Foo hides Actifs:Chèque:Foo
    j.add_accounts([Account(qname='Chèque'),
                    Account(qname='Chèque:Foo')])

    assert j.chartOfAccounts.short_qname('Actifs:Chèque:Foo').qstr == 'Actifs:Chèque:Foo'
    assert j.chartOfAccounts.short_qname('Chèque:Foo').qstr == 'Chèque:Foo'
    assert j.chartOfAccounts.full_qname('Chèque:Foo').qstr == 'Chèque:Foo'
    assert j.chartOfAccounts.account('Chèque:Foo').qname.qstr == 'Chèque:Foo'


def test_duplicate_balance():
    j = Journal()
    j.add_accounts([Account(qname='Actifs')])
    j.add_bassertions([BAssertion(date=date(2021, 1, 1), acc_qname='Actifs', balance=Decimal(100))])
    with pytest.raises(ValueError):
        j.add_bassertions([BAssertion(date=date(2021, 1, 1), acc_qname='Actifs',
                                      balance=Decimal(100))])

    j.add_accounts([Account(qname='Actifs:Chèque')])
    j.add_bassertions([BAssertion(date=date(2021, 1, 1), acc_qname='Actifs:Chèque',
                                  balance=Decimal(100))])
    with pytest.raises(ValueError):
        j.add_bassertions([BAssertion(date=date(2021, 1, 1), acc_qname='Chèque',
                                      balance=Decimal(100))])


def test_write_txns(accounts_file, txns_file, tmp_path):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    tmp_file = tmp_path / 'txns.csv'
    j.write_txns(filefunc=tmp_file)
    with open(tmp_file, 'r') as f:
        header = f.readline()
    assert header == 'No txn,Date,Compte,Montant,Date du relevé,Commentaire,Description du relevé\n'


def test_export_txns(accounts_file, txns_file, tmp_path):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    tmp_file = tmp_path / 'txns.csv'
    j.export_txns(file=tmp_file)

    j2 = Journal.from_csv(accounts=accounts_file, postings=tmp_file)
    assert len(list(j.txns)) == len(list(j2.txns))
    txns = list(j2.txns)
    assert "Numéro" in txns[0].postings[0].tags


def test_write_balances(accounts_file, bassertions_file, tmp_path):
    j = Journal.from_csv(accounts=accounts_file, postings=[], bassertions=bassertions_file)
    tmp_file = tmp_path / 'bassertions.csv'
    j.write_bassertions(file=tmp_file)
    with open(tmp_file, 'r') as f:
        header = f.readline()
    assert header == 'Date,Compte,Solde,Commentaire\n'


def test_write_accounts(accounts_file, tmp_path):
    j = Journal.from_csv(accounts=accounts_file, postings=[])
    tmp_file = tmp_path / 'accounts.csv'
    j.write_accounts(file=tmp_file)
    with open(tmp_file, 'r') as f:
        header = f.readline()
    assert header == 'Compte,Numéro,Tag 1\n'


def test_too_many_columns(accounts_too_many_columns):
    with pytest.raises(ValueError):
        Journal.from_csv(accounts=accounts_too_many_columns)


def test_flow(accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    assert j.flow(date(2021, 1, 1), date(2021, 1, 31), 'Actifs:Chèque') == Decimal(2460)
    assert j.flow(date(2021, 1, 1), date(2021, 1, 1), 'Actifs:Chèque') == Decimal(2500)
    assert j.flow(date(2021, 1, 5), date(2021, 1, 31), 'Actifs:Chèque') == Decimal(0)
    assert j.flow(date(2021, 1, 1), date(2021, 1, 31), 'Actifs:Épargne') == Decimal(15000)
    assert j.flow(date(2021, 1, 1), date(2021, 1, 31), 'Actifs:Maison') == Decimal(450000)
    assert j.flow(date(2021, 1, 1), date(2021, 1, 31), 'Actifs') == Decimal(467460)
    with pytest.raises(ValueError):
        j.flow(date(2021, 1, 31), date(2021, 1, 1), 'Actifs:Chèque')
