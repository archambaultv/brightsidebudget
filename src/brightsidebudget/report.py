import csv
from datetime import date, timedelta
from decimal import Decimal
from typing import Callable
from bs4 import BeautifulSoup
from brightsidebudget.account import Account
from brightsidebudget.journal import Journal
from brightsidebudget.posting import Posting
from brightsidebudget.utils import csv_to_excel


class RParams:
    def __init__(self, end_of_years: list[date],
                 column_amnt: Callable[[Journal, Account, date], str],
                 total_name: str,
                 total_type: str,
                 normalize_sign: Callable[[str], Decimal] | None = None,
                 account_alias: Callable[[Account], Account | None] | None = None,
                 type_emoji: dict[str, str] | None = None):
        self.end_of_years = end_of_years
        self.column_amnt = column_amnt
        self.total_name = total_name
        self.total_type = total_type
        self.type_emoji = type_emoji or {}

        def _default_normalize_sign(_: str) -> Decimal:
            return Decimal(1)

        self.normalize_sign = normalize_sign or _default_normalize_sign

        def _default_account_alias(a: Account) -> Account:
            return a

        self.account_alias = account_alias or _default_account_alias

    @classmethod
    def balance_sheet(cls, *, end_of_years: list[date],
                      account_alias: Callable[[Account], Account | None] | None = None
                      ) -> 'RParams':
        def _normalize_sign(t: str) -> Decimal:
            if t == "Passifs":
                return Decimal(-1)
            return Decimal(1)

        def _account_alias(a: Account) -> Account | None:
            if a.type in ["Actifs", "Passifs"]:
                return a
            return None

        return cls(end_of_years=end_of_years,
                   column_amnt=lambda j, a, e: j.balance(a, e),
                   total_name="Valeur nette",
                   total_type="Actifs",
                   account_alias=account_alias or _account_alias,
                   normalize_sign=_normalize_sign,
                   type_emoji={"Actifs": "💰", "Passifs": "💳"})

    @classmethod
    def income_stmt(cls, *, end_of_years: list[date],
                    account_alias: Callable[[Account], Account | None] | None = None
                    ) -> 'RParams':
        def _normalize_sign(t: str) -> Decimal:
            if t in ["Revenus"]:
                return Decimal(-1)
            return Decimal(1)

        def _flow(j: Journal, a: Account, e: date) -> Decimal:
            s = e.replace(year=e.year - 1) + timedelta(days=1)
            return j.flow(a, s, e)

        def _account_alias(a: Account) -> Account | None:
            if a.type in ["Revenus", "Dépenses"]:
                return a
            return None

        return cls(end_of_years=end_of_years,
                   column_amnt=_flow,
                   total_type="Revenus",
                   normalize_sign=_normalize_sign,
                   account_alias=account_alias or _account_alias,
                   type_emoji={"Revenus": "💰", "Dépenses": "💳"},
                   total_name="Résultat")

    @classmethod
    def flow_stmt(cls, *, end_of_years: list[date],
                  account_alias: Callable[[Account], Account | None] | None = None
                  ) -> 'RParams':

        def _flow(j: Journal, a: Account, e: date) -> Decimal:
            s = e.replace(year=e.year - 1) + timedelta(days=1)
            return j.flow(a, s, e)

        def _account_alias(a: Account) -> Account | None:
            if a.type in ["Actifs", "Passifs"]:
                return a
            return None

        return cls(end_of_years=end_of_years,
                   column_amnt=_flow,
                   total_type="Actifs",
                   account_alias=account_alias or _account_alias,
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


def _mk_table(end_of_years: list[date], body_rows: list[str], footer: str) -> str:
    header = _table_header(end_of_years)
    body = "<tbody>" + "".join(body_rows) + "</tbody>"
    foot = "<tfoot>" + footer + "</tfoot>"
    return _pretty_html(f"<table>{header}{body}{foot}</table>")


def generic_report(j: Journal, params: RParams) -> str:
    # Compute the values, aggregated by account alias
    d: dict[Account, list[Decimal]] = {}
    for a in j.accounts:
        acc_alias = params.account_alias(a)
        if acc_alias is None:
            continue

        if acc_alias not in d:
            d[acc_alias] = [Decimal(0) for _ in params.end_of_years]

        for i, e in enumerate(params.end_of_years):
            s = params.column_amnt(j, a, e)
            d[acc_alias][i] += s

    # Find the types present in d and compute the subtotals
    # and rows
    types = sorted({a.type for a in d.keys()}, key=Account.type_sort_key)
    body_rows: list[str] = []
    for t in types:
        sign = params.normalize_sign(t)
        d2 = {}
        for a, v in d.items():
            if a.type == t:
                d2[a.name] = [sign * x for x in v]

        # Skip if all values are 0
        if all(x == 0 for v in d2.values() for x in v):
            continue

        # Compute the subtotal
        sub_totals: list[Decimal] = [Decimal(0) for _ in params.end_of_years]
        for k, v in d2.items():
            for i, x in enumerate(v):
                sub_totals[i] += x
        type_emoji = params.type_emoji.get(t, "")
        col_name = f"<strong>{type_emoji} {t}</strong>"
        body_rows.append(_mk_row([col_name] + [f"<strong>{_n(t)}</strong>" for t in sub_totals]))

        # Add the account rows
        for k, v in sorted(d2.items(), key=lambda x: x[1][-1], reverse=True):
            if all(x == 0 for x in v):
                continue
            body_rows += _mk_row([f"&emsp;{k}"] + [_n(t) for t in v])

    # Total
    big_totals: list[Decimal] = [Decimal(0) for _ in params.end_of_years]
    for v in d.values():
        for i, x in enumerate(v):
            big_totals[i] += x
    sign = params.normalize_sign(params.total_type)
    big_totals = [sign * x for x in big_totals]
    footer = _mk_row([f"<strong>🚀 {params.total_name}</strong>"] +
                     [f"<strong>{_n(t)}</strong>" for t in big_totals])

    return _mk_table(params.end_of_years, body_rows, footer)


def export_txns(j: Journal, filename: str, filter: Callable[[Posting], bool] = None) -> None:
    if filter is None:
        def filter(_):
            return True

    header = Posting.header() + ["Année fiscale"] + Account.header()[1:]
    with open(filename, "w", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        for t in j.txns():
            if not filter(t):
                continue
            for p in t.postings:
                d = p.to_dict()
                d["Date du relevé"] = str(p.stmt_date)
                d["Année fiscale"] = str(j.fiscal_year(p.date))
                a = p.account.to_dict()
                del a["Compte"]
                d.update(a)
                writer.writerow(d)
    csv_to_excel(filename)
