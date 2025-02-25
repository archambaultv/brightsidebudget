from datetime import date, timedelta
from decimal import Decimal
from typing import Callable
from bs4 import BeautifulSoup
from brightsidebudget.account import Account
from brightsidebudget.journal import Journal
from brightsidebudget.txn import Txn


class RParams:
    def __init__(self, end_of_years: list[date],
                 merge_accounts: dict[Account, Account] | None = None,
                 exclude_txns: Callable[[Txn], bool] | None = None):
        self.end_of_years = end_of_years
        self.merge_accounts = merge_accounts or {}
        self.exclude_txns = exclude_txns or (lambda x: False)

    def merged_account(self, account: Account) -> Account:
        return self.merge_accounts.get(account, account)

    def is_excluded_txn(self, txn: Txn) -> bool:
        return self.exclude_txns(txn)


def _n(x: Decimal) -> str:
    return f"{x:,.0f}".replace(",", "&nbsp;")


def _mk_row(ls: list[str]) -> str:
    return "<tr><td>" + "</td><td>".join(ls) + "</td></tr>\n"


def _pretty_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.prettify()


def _table_header(end_of_years: list[date]) -> str:
    # Year header
    header = ("<tr>\n" +
              "\n".join(["<th>Compte</th>"] + [f"<th>{e.year}</th>" for e in end_of_years]) +
              "</tr>\n")
    return header


def balance_sheet(j: Journal, params: RParams) -> str:
    """
    Generate an HTML balance sheet report
    """

    # Year header
    report = "<table>\n"
    report += _table_header(params.end_of_years)

    # Assets and liabilities
    big_totals: list[Decimal] = [Decimal(0) for _ in params.end_of_years]
    for t in ["Actifs", "Passifs"]:
        totals: list[Decimal] = [Decimal(0) for _ in params.end_of_years]
        d: dict[str, list[Decimal]] = {}
        for a in j.accounts:
            macc = params.merged_account(a)
            if macc.type != t:
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
            col_name = f"<strong>💰 {t}</strong>"
        else:
            col_name = f"<strong>💳 {t}</strong>"
        report += _mk_row([col_name] + [f"<strong>{_n(t)}</strong>" for t in totals])
        for k, v in sorted(d.items(), key=lambda x: x[1][-1], reverse=True):
            if all(x == 0 for x in v):
                continue
            report += _mk_row([f"&emsp;{k}"] + [_n(t) for t in v])

    # Total
    report += _mk_row(["<strong>🚀 Valeur nette</strong>"] +
                      [f"<strong>{_n(t)}</strong>" for t in big_totals])
    report += "</table>"

    return _pretty_html(report)


def income_stmt(j: Journal, params: RParams) -> str:
    """
    Generate an HTML income statement report
    """

    # Year header
    report = "<table>\n"
    report += _table_header(params.end_of_years)

    # Revenues and expenses
    big_totals: list[Decimal] = [Decimal(0) for _ in params.end_of_years]
    for t in ["Revenus", "Dépenses"]:
        totals: list[Decimal] = [Decimal(0) for _ in params.end_of_years]
        d: dict[str, list[Decimal]] = {}
        for a in j.accounts:
            macc = params.merged_account(a)
            if macc.type != t:
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
            col_name = f"<strong>💰 {t}</strong>"
        else:
            col_name = f"<strong>💳 {t}</strong>"
        report += _mk_row([col_name] + [f"<strong>{_n(t)}</strong>" for t in totals])
        for k, v in sorted(d.items(), key=lambda x: x[1][-1], reverse=True):
            if all(x == 0 for x in v):
                continue
            report += _mk_row([f"&emsp;{k}"] + [_n(t) for t in v])

    # Total
    report += _mk_row(["<strong>🚀 Résultat</strong>"] +
                      [f"<strong>{_n(t)}</strong>" for t in big_totals])
    report += "</table>"

    return _pretty_html(report)


def flow_stmt(j: Journal, params: RParams) -> str:
    """
    Generate an HTML flow statement report
    """

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
    report = "<table>\n"
    report += _table_header(params.end_of_years)

    # Assets and liabilities
    big_totals: list[Decimal] = [Decimal(0) for _ in params.end_of_years]
    for t in ["Actifs", "Passifs"]:
        totals: list[Decimal] = [Decimal(0) for _ in params.end_of_years]
        d: dict[str, list[Decimal]] = {}
        for a in j.accounts:
            macc = params.merged_account(a)
            if macc.type != t:
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
            col_name = f"<strong>💰 {t}</strong>"
        else:
            col_name = f"<strong>💳 {t}</strong>"
        report += _mk_row([col_name] + [f"<strong>{_n(t)}</strong>" for t in totals])
        for k, v in sorted(d.items(), key=lambda x: x[1][-1], reverse=True):
            if all(x == 0 for x in v):
                continue
            report += _mk_row([f"&emsp;{k}"] + [_n(t) for t in v])

    # Total
    report += _mk_row(["<strong>🚀 Résultat</strong>"] +
                      [f"<strong>{_n(t)}</strong>" for t in big_totals])
    report += "</table>"

    return _pretty_html(report)
