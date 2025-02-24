from datetime import date, timedelta
from decimal import Decimal
from typing import Callable
from brightsidebudget.account import Account
from brightsidebudget.journal import Journal
from brightsidebudget.txn import Txn


class RParams:
    def __init__(self, end_of_years: list[date],
                 merge_accounts: dict[Account, Account] | None = None,
                 exclude_accounts: list[Account] | None = None,
                 exclude_txns: Callable[[Txn], bool] | None = None):
        self.end_of_years = end_of_years
        self.merge_accounts = merge_accounts or {}
        self.exclude_accounts = exclude_accounts or []
        self.exclude_txns = exclude_txns or (lambda x: False)

    def merged_account(self, account: Account) -> Account:
        return self.merge_accounts.get(account, account)

    def is_excluded_account(self, account: Account) -> bool:
        return account in self.exclude_accounts

    def is_excluded_txn(self, txn: Txn) -> bool:
        return self.exclude_txns(txn)


def balance_sheet(j: Journal, params: RParams) -> str:
    """
    Generate a markdown balance sheet report
    """
    report = "# Bilan\n\n"

    def n(x: Decimal) -> str:
        return f"{x:,.0f}".replace(",", " ")

    def mk_col(ls: list[str]) -> str:
        return "| " + " | ".join(ls) + " |\n"

    # Year header
    ls = ["Compte"]
    for e in params.end_of_years:
        ls.append(f"{e.year}")
    report += mk_col(ls)
    report += mk_col([":---"] + ["---:" for _ in ls[1:]])

    # Assets and liabilities
    big_totals: list[Decimal] = [Decimal(0) for _ in params.end_of_years]
    for t in ["Actifs", "Passifs"]:
        totals: list[Decimal] = [Decimal(0) for _ in params.end_of_years]
        d: dict[str, list[Decimal]] = {}
        for a in j.accounts:
            macc = params.merged_account(a)
            if macc.type != t or params.is_excluded_account(macc):
                continue

            if macc.name not in d:
                d[macc.name] = [Decimal(0) for _ in params.end_of_years]
            for i, e in enumerate(params.end_of_years):
                s = j.balance(a, e)
                big_totals[i] += s
                if t == "Passifs":
                    s = -s
                totals[i] += s
                d[macc.name][i] += s

        if t == "Actifs":
            col_name = f"💰 *{t}*"
        else:
            col_name = f"💳 *{t}*"
        report += mk_col([col_name] + [n(t) for t in totals])
        for k, v in sorted(d.items(), key=lambda x: x[1][-1], reverse=True):
            if all(x == 0 for x in v):
                continue
            report += mk_col([f"&emsp;{k}"] + [n(t) for t in v])

    # Total
    report += mk_col(["**🚀 Valeur nette**"] + [f"**{n(t)}**" for t in big_totals])

    return report


def income_stmt(j: Journal, params: RParams) -> str:
    """
    Generate a markdown income statement report
    """
    report = "# État des résultats\n\n"

    def n(x: Decimal) -> str:
        return f"{x:,.0f}".replace(",", " ")

    def mk_col(ls: list[str]) -> str:
        return "| " + " | ".join(ls) + " |\n"

    # Year header
    ls = ["Compte"]
    for e in params.end_of_years:
        ls.append(f"{e.year}")
    report += mk_col(ls)
    report += mk_col([":---"] + ["---:" for _ in ls[1:]])

    # Assets and liabilities
    big_totals: list[Decimal] = [Decimal(0) for _ in params.end_of_years]
    for t in ["Revenus", "Dépenses"]:
        totals: list[Decimal] = [Decimal(0) for _ in params.end_of_years]
        d: dict[str, list[Decimal]] = {}
        for a in j.accounts:
            macc = params.merged_account(a)
            if macc.type != t or params.is_excluded_account(macc):
                continue

            if macc.name not in d:
                d[macc.name] = [Decimal(0) for _ in params.end_of_years]
            for i, e in enumerate(params.end_of_years):
                start = e.replace(year=e.year - 1) + timedelta(days=1)
                s = j.flow(a, start, e)
                big_totals[i] -= s
                if t == "Revenus":
                    s = -s
                totals[i] += s
                d[macc.name][i] += s

        if t == "Revenus":
            col_name = f"💰 *{t}*"
        else:
            col_name = f"💳 *{t}*"
        report += mk_col([col_name] + [n(t) for t in totals])
        for k, v in sorted(d.items(), key=lambda x: x[1][-1], reverse=True):
            if all(x == 0 for x in v):
                continue
            report += mk_col([f"&emsp;{k}"] + [n(t) for t in v])

    # Total
    report += mk_col(["**🚀 Résultat**"] + [f"**{n(t)}**" for t in big_totals])

    return report


def flow_stmt(j: Journal, params: RParams) -> str:
    """
    Generate a markdown flow statement report
    """
    report = "# Flux financiers\n\n"

    def n(x: Decimal) -> str:
        return f"{x:,.0f}".replace(",", " ")

    def mk_col(ls: list[str]) -> str:
        return "| " + " | ".join(ls) + " |\n"

    def flow(a: Account, start: date, end: date) -> Decimal:
        s = Decimal(0)
        for t in j.txns():
            if params.is_excluded_txn(t):
                continue
            for p in t:
                if p.account == a and start <= p.date <= end:
                    s += p.amount
        return s

    # Year header
    ls = ["Compte"]
    for e in params.end_of_years:
        ls.append(f"{e.year}")
    report += mk_col(ls)
    report += mk_col([":---"] + ["---:" for _ in ls[1:]])

    # Assets and liabilities
    big_totals: list[Decimal] = [Decimal(0) for _ in params.end_of_years]
    for t in ["Actifs", "Passifs"]:
        totals: list[Decimal] = [Decimal(0) for _ in params.end_of_years]
        d: dict[str, list[Decimal]] = {}
        for a in j.accounts:
            macc = params.merged_account(a)
            if macc.type != t or macc in params.exclude_accounts:
                continue

            if macc.name not in d:
                d[macc.name] = [Decimal(0) for _ in params.end_of_years]
            for i, e in enumerate(params.end_of_years):
                start = e.replace(year=e.year - 1) + timedelta(days=1)
                s = flow(a, start, e)
                big_totals[i] += s
                totals[i] += s
                d[macc.name][i] += s

        if t == "Actifs":
            col_name = f"💰 *{t}*"
        else:
            col_name = f"💳 *{t}*"
        report += mk_col([col_name] + [n(t) for t in totals])
        for k, v in sorted(d.items(), key=lambda x: x[1][-1], reverse=True):
            if all(x == 0 for x in v):
                continue
            report += mk_col([f"&emsp;{k}"] + [n(t) for t in v])

    # Total
    report += mk_col(["**🚀 Résultat**"] + [f"**{n(t)}**" for t in big_totals])

    return report
