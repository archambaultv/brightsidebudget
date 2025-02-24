from datetime import date, timedelta
from decimal import Decimal
from brightsidebudget.posting import Posting
from brightsidebudget.account import Account
from brightsidebudget.txn import Txn
from brightsidebudget.journal import Journal
from brightsidebudget.report import balance_sheet, RParams, flow_stmt, income_stmt


def test_balance_sheet():
    j = Journal()
    a1 = Account(name="A1", number=1001, type="Actifs", group="Groupe", sub_group="Sous-groupe")
    a2 = Account(name="P1", number=2001, type="Passifs", group="Groupe", sub_group="Sous-groupe")
    a3 = Account(name="A2", number=1003, type="Actifs", group="Groupe", sub_group="Sous-groupe")
    a4 = Account(name="P2", number=2002, type="Passifs", group="Groupe", sub_group="Sous-groupe")
    j.add_account(a1)
    j.add_account(a2)
    j.add_account(a3)
    j.add_account(a4)

    for i in range(1, 13):
        dt = date(2024, 12, 27) + timedelta(days=i)
        p1 = Posting(txn_id=i*2, date=dt, account=a1, amount=Decimal(100))
        p2 = Posting(txn_id=i*2, date=dt, account=a2, amount=Decimal(-100))
        t = Txn(postings=[p1, p2])
        j.add_txn(t)

        p1 = Posting(txn_id=i*2+1, date=dt, account=a3, amount=Decimal(1))
        p2 = Posting(txn_id=i*2+1, date=dt, account=a4, amount=Decimal(-1))
        t = Txn(postings=[p1, p2])
        j.add_txn(t)

    params = RParams(end_of_years=[date(2024, 12, 31), date(2025, 12, 31)],
                     merge_accounts={a3: a1})
    rep = balance_sheet(j, params)
    with open("tests/reports/balance_sheet.html", 'r', encoding="utf-8") as f:
        expected = f.read()
    assert rep == expected


def test_income_stmt():
    j = Journal()
    a1 = Account(name="R1", number=1001, type="Revenus", group="Groupe", sub_group="Sous-groupe")
    a2 = Account(name="D1", number=2001, type="Dépenses", group="Groupe", sub_group="Sous-groupe")
    a3 = Account(name="R2", number=1003, type="Revenus", group="Groupe", sub_group="Sous-groupe")
    a4 = Account(name="D2", number=2002, type="Dépenses", group="Groupe", sub_group="Sous-groupe")
    j.add_account(a1)
    j.add_account(a2)
    j.add_account(a3)
    j.add_account(a4)

    for i in range(1, 13):
        dt = date(2024, 12, 27) + timedelta(days=i)
        p1 = Posting(txn_id=i*2, date=dt, account=a1, amount=Decimal(-100))
        p2 = Posting(txn_id=i*2, date=dt, account=a2, amount=Decimal(100))
        t = Txn(postings=[p1, p2])
        j.add_txn(t)

        p1 = Posting(txn_id=i*2+1, date=dt, account=a3, amount=Decimal(-1))
        p2 = Posting(txn_id=i*2+1, date=dt, account=a4, amount=Decimal(1))
        t = Txn(postings=[p1, p2])
        j.add_txn(t)

    params = RParams(end_of_years=[date(2024, 12, 31), date(2025, 12, 31)],
                     merge_accounts={a3: a1})
    rep = income_stmt(j, params)
    with open("tests/reports/income_stmt.html", 'r', encoding="utf-8") as f:
        expected = f.read()
    assert rep == expected


def test_flow_stmt():
    j = Journal()
    a1 = Account(name="A1", number=1001, type="Actifs", group="Groupe", sub_group="Sous-groupe")
    a2 = Account(name="P1", number=2001, type="Passifs", group="Groupe", sub_group="Sous-groupe")
    a3 = Account(name="A2", number=1003, type="Actifs", group="Groupe", sub_group="Sous-groupe")
    a4 = Account(name="P2", number=2002, type="Passifs", group="Groupe", sub_group="Sous-groupe")
    j.add_account(a1)
    j.add_account(a2)
    j.add_account(a3)
    j.add_account(a4)

    for i in range(1, 13):
        dt = date(2024, 12, 27) + timedelta(days=i)
        p1 = Posting(txn_id=i*2, date=dt, account=a1, amount=Decimal(100))
        p2 = Posting(txn_id=i*2, date=dt, account=a2, amount=Decimal(-100))
        t = Txn(postings=[p1, p2])
        j.add_txn(t)

        p1 = Posting(txn_id=i*2+1, date=dt, account=a3, amount=Decimal(1))
        p2 = Posting(txn_id=i*2+1, date=dt, account=a4, amount=Decimal(-1))
        t = Txn(postings=[p1, p2])
        j.add_txn(t)

    params = RParams(end_of_years=[date(2024, 12, 31), date(2025, 12, 31)],
                     merge_accounts={a3: a1})
    rep = flow_stmt(j, params)
    with open("tests/reports/flow_stmt.html", 'r', encoding="utf-8") as f:
        expected = f.read()
    assert rep == expected
