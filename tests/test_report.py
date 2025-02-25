from datetime import date, timedelta
from decimal import Decimal
import os
from brightsidebudget.posting import Posting
from brightsidebudget.account import Account
from brightsidebudget.txn import Txn
from brightsidebudget.journal import Journal
from brightsidebudget.report import RParams, export_txns, generic_report


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

    end_of_years = [date(2024, 12, 31), date(2025, 12, 31)]

    def account_alias(a: Account) -> Account:
        if a == a3:
            return a1
        return a
    p = RParams.balance_sheet(end_of_years=end_of_years, account_alias=account_alias)
    rep = generic_report(j, p)
    # with open("tests/reports/balance_sheet.html", 'w', encoding="utf-8") as f:
    #     f.write(rep)
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

    end_of_years = [date(2024, 12, 31), date(2025, 12, 31)]

    def account_alias(a: Account) -> Account:
        if a == a3:
            return a1
        return a
    p = RParams.income_stmt(end_of_years=end_of_years, account_alias=account_alias)
    rep = generic_report(j, p)
    # with open("tests/reports/income_stmt.html", 'w', encoding="utf-8") as f:
    #     f.write(rep)
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

    end_of_years = [date(2024, 12, 31), date(2025, 12, 31)]

    def account_alias(a: Account) -> Account:
        if a == a3:
            return a1
        return a

    p = RParams.flow_stmt(end_of_years=end_of_years, account_alias=account_alias)
    rep = generic_report(j, p)
    # with open("tests/reports/flow_stmt.html", 'w', encoding="utf-8") as f:
    #     f.write(rep)
    with open("tests/reports/flow_stmt.html", 'r', encoding="utf-8") as f:
        expected = f.read()
    assert rep == expected


def test_export_txns(tmp_path):
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

    filename = os.path.join(tmp_path, "export_txns.csv")
    export_txns(j, filename)
    with open(filename, 'r', encoding="utf-8") as f:
        rep = f.read()
    with open("tests/reports/export_txns.csv", 'r', encoding="utf-8") as f:
        expected = f.read()
    assert rep == expected
