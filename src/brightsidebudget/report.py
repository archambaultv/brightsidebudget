import csv
from datetime import date, timedelta
from decimal import Decimal
from typing import Callable
from bs4 import BeautifulSoup
from brightsidebudget.account import Account
from brightsidebudget.journal import Journal
from brightsidebudget.posting import Posting
from brightsidebudget.txn import Txn
from brightsidebudget.utils import csv_to_excel


class RParams:
    def __init__(self, end_of_years: list[date],
                 account_types: list[str],
                 column_amnt: Callable[[Journal, Account, date], str],
                 total_name: str,
                 normalize_sign: Callable[[Decimal, Account | str], Decimal] | None = None,
                 account_alias: Callable[[Account], Account] | None = None,
                 type_emoji: dict[str, str] | None = None,
                 exclude_txn: Callable[[Txn], bool] | None = None):
        self.end_of_years = end_of_years
        self.account_types = account_types
        self.column_amnt = column_amnt
        self.total_name = total_name
        self.type_emoji = type_emoji or {}

        def _default_normalize_sign(x: Decimal, _: Account | str) -> Decimal:
            return x

        self.normalize_sign = normalize_sign or _default_normalize_sign

        def _default_account_alias(a: Account) -> Account:
            return a

        self.account_alias = account_alias or _default_account_alias

        def _default_exclude_txn(t: Txn) -> bool:
            return False

        self.exclude_txn = exclude_txn or _default_exclude_txn

    @classmethod
    def balance_sheet(cls, *, end_of_years: list[date],
                      account_alias: Callable[[Account], Account] | None = None,
                      exclude_txn: Callable[[Txn], bool] | None = None) -> 'RParams':
        def _normalize_sign(x: Decimal, a: Account | str) -> Decimal:
            if isinstance(a, Account):
                a = a.type
            if a == "Passifs":
                return -x
            return x

        return cls(end_of_years=end_of_years,
                   account_types=["Actifs", "Passifs"],
                   column_amnt=lambda j, a, e: j.balance(a, e),
                   total_name="Valeur nette",
                   account_alias=account_alias,
                   exclude_txn=exclude_txn,
                   normalize_sign=_normalize_sign,
                   type_emoji={"Actifs": "💰", "Passifs": "💳"})

    @classmethod
    def income_stmt(cls, *, end_of_years: list[date],
                    account_alias: Callable[[Account], Account] | None = None,
                    exclude_txn: Callable[[Txn], bool] | None = None) -> 'RParams':
        def _normalize_sign(x: Decimal, a: Account | str) -> Decimal:
            if isinstance(a, Account):
                a = a.type
            if a in ["Revenus", "Total"]:
                return -x
            return x

        def _flow(j: Journal, a: Account, e: date) -> Decimal:
            s = e.replace(year=e.year - 1) + timedelta(days=1)
            return j.flow(a, s, e)

        return cls(end_of_years=end_of_years,
                   account_types=["Revenus", "Dépenses"],
                   column_amnt=_flow,
                   normalize_sign=_normalize_sign,
                   account_alias=account_alias,
                   exclude_txn=exclude_txn,
                   type_emoji={"Revenus": "💰", "Dépenses": "💳"},
                   total_name="Résultat")

    @classmethod
    def flow_stmt(cls, *, end_of_years: list[date],
                  account_alias: Callable[[Account], Account] | None = None,
                  exclude_txn: Callable[[Txn], bool] | None = None) -> 'RParams':

        def _flow(j: Journal, a: Account, e: date) -> Decimal:
            s = e.replace(year=e.year - 1) + timedelta(days=1)
            return j.flow(a, s, e)

        return cls(end_of_years=end_of_years,
                   account_types=["Actifs", "Passifs"],
                   column_amnt=_flow,
                   account_alias=account_alias,
                   exclude_txn=exclude_txn,
                   type_emoji={"Actifs": "💰", "Passifs": "💳"},
                   total_name="Résultat")


def _n(x: Decimal) -> str:
    return f"{x:,.0f}".replace(",", "&nbsp;")


def _mk_row(ls: list[str]) -> str:
    if not ls:
        return ""
    return "<tr><td>" + "</td><td>".join(ls) + "</td></tr>"


def _pretty_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.prettify()


def _table_header(end_of_years: list[date]) -> str:
    # Year header
    header = ("<thead>" +
              "".join(["<th>Compte</th>"] + [f"<th>{e.year}</th>" for e in end_of_years]) +
              "</thead>")
    return header


def _mk_table(end_of_years: list[date], body_rows: list[str]) -> str:
    header = _table_header(end_of_years)
    body = "<tbody>" + "".join(body_rows) + "</tbody>"
    return _pretty_html(f"<table>{header}{body}</table>")


def generic_report(j: Journal, params: RParams) -> str:

    body_rows: list[str] = []
    # Assets and liabilities
    big_totals: list[Decimal] = [Decimal(0) for _ in params.end_of_years]
    for t in params.account_types:
        sub_totals: list[Decimal] = [Decimal(0) for _ in params.end_of_years]
        d: dict[str, list[Decimal]] = {}
        for a in j.accounts:
            macc = params.account_alias(a)
            if macc.type != t:
                continue

            if macc.name not in d:
                d[macc.name] = [Decimal(0) for _ in params.end_of_years]
            for i, e in enumerate(params.end_of_years):
                s = params.column_amnt(j, a, e)
                big_totals[i] += params.normalize_sign(s, "Total")
                sub_totals[i] += params.normalize_sign(s, t)
                d[macc.name][i] += params.normalize_sign(s, a)

        # Skip this type if all values are zero
        if all(x == 0 for v in d.values() for x in v):
            continue

        # Add the type subtotals
        type_emoji = params.type_emoji.get(t, "")
        col_name = f"<strong>{type_emoji} {t}</strong>"
        body_rows.append(_mk_row([col_name] + [f"<strong>{_n(t)}</strong>" for t in sub_totals]))

        # Add the account rows
        for k, v in sorted(d.items(), key=lambda x: x[1][-1], reverse=True):
            if all(x == 0 for x in v):
                continue
            body_rows += _mk_row([f"&emsp;{k}"] + [_n(t) for t in v])

    # Total
    body_rows.append(_mk_row([f"<strong>🚀 {params.total_name}</strong>"] +
                             [f"<strong>{_n(t)}</strong>" for t in big_totals]))

    return _mk_table(params.end_of_years, body_rows)


def export_txns(j: Journal, filename: str):
    header = Posting.header() + ["Année fiscale"] + Account.header()[1:]
    with open(filename, "w", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        for p in j.postings:
            d = p.to_dict()
            d["Date du relevé"] = str(p.stmt_date)
            d["Année fiscale"] = str(j.fiscal_year(p.date))
            a = p.account.to_dict()
            del a["Compte"]
            d.update(a)
            writer.writerow(d)
    csv_to_excel(filename)
