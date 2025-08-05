
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Union

from pydantic import BaseModel, model_validator
import xlsxwriter
import polars as pl

from brightsidebudget.account.account import Account
from brightsidebudget.bassertion import BAssertion
from brightsidebudget.txn.posting import Posting
from brightsidebudget.txn.txn import Txn


class Journal(BaseModel):
    

    accounts: list[Account]
    txns: list[Txn]
    bassertions: list[BAssertion]

    @model_validator(mode='after')
    def validate_journal(self):
        # Unique account names
        names: set = set()
        for a in self.accounts:
            if a.name in names:
                raise ValueError(f"Duplicate account name: {a.name}")
            names.add(a.name)

        # Unique account numbers
        numbers: set = set()
        for a in self.accounts:
            if a.number in numbers:
                raise ValueError(f"Duplicate account number: {a.number}")
            numbers.add(a.number)

        # Unique transaction IDs
        txn_ids: set = set()
        for t in self.txns:
            if t.txn_id in txn_ids:
                raise ValueError(f"Duplicate transaction ID: {t.txn_id}")
            txn_ids.add(t.txn_id)

        # Unique assertion keys
        assertion_keys: set = set()
        for b in self.bassertions:
            key = b.dedup_key()
            if key in assertion_keys:
                raise ValueError(f"Duplicate assertion key: {key}")
            assertion_keys.add(key)

        return self

    def add_txn(self, txn: Txn) -> None:
        """
        Adds a transaction to the journal.
        """
        if txn.txn_id in (t.txn_id for t in self.txns):
            raise ValueError(f"Transaction ID {txn.txn_id} already exists in journal")
        self.txns.append(txn)

    def add_bassertion(self, bassertion: BAssertion) -> None:
        """
        Adds a balance assertion to the journal.
        """
        if bassertion.dedup_key() in (b.dedup_key() for b in self.bassertions):
            raise ValueError(f"Balance assertion for {bassertion.account.name} on {bassertion.date} already exists")
        self.bassertions.append(bassertion)

    def get_accounts_dict(self) -> dict[str, Account]:
        return {a.name: a for a in self.accounts}

    def get_txn_dict(self) -> dict[int, Txn]:
        return {t.txn_id: t for t in self.txns}

    def get_postings(self) -> list[Posting]:
        return [posting for txn in self.txns for posting in txn.postings]

    def get_account(self, account: str) -> Account:
        for a in self.accounts:
            if a.name == account:
                return a
        raise ValueError(f"Account '{account}' not found in journal")

    def account_balance(self, account: str | Account, date: date,
                use_stmt_date: bool = False) -> Decimal:
        if isinstance(account, Account):
            account = account.name

        def get_date(p: Posting):
            return p.stmt_date if use_stmt_date else p.date

        s = sum((p.amount for p in self.get_postings()
                if p.account.name == account and get_date(p) <= date),
                start=Decimal(0))
        return s

    def account_flow(self, account: str | Account,
             start_date: date, end_date: date) -> Decimal:
        if isinstance(account, Account):
            account = account.name
        s = sum((p.amount for p in self.get_postings()
                if p.account.name == account
                and p.date <= end_date
                and p.date >= start_date),
                start=Decimal(0))
        return s

    def next_txn_id(self) -> int:
        return max((p.txn_id for p in self.get_postings()), default=0) + 1

    def known_keys(self) -> dict[tuple[date, str, Decimal, str], int]:
        known = defaultdict(int)
        for p in self.get_postings():
            known[p.dedup_key()] += 1
        return known

    def get_last_balance(self, account: str | Account) -> Union['BAssertion', None]:
        if isinstance(account, Account):
            account = account.name
        last = None
        for b in self.bassertions:
            if b.account.name == account:
                if last is None or b.date > last.date:
                    last = b
        return last

    def failed_bassertions(self) -> list[BAssertion]:
        errors = []
        for b in self.bassertions:
            s = self.account_balance(b.account, b.date, use_stmt_date=True)
            if s != b.balance:
                errors.append(b)
        return errors

    def find_subset(self, *,
                    amnt: Decimal,
                    account: str | Account,
                    start_date: date,
                    end_date: date,
                    use_stmt_date: bool = False) -> list['Posting'] | None:
        """
        Finds a subset of postings that sum to the given amount.
        """
        if isinstance(account, Account):
            account = account.name

        def get_date(p: Posting) -> date:
            return p.stmt_date if use_stmt_date else p.date

        ps = [p for p in self.get_postings()
              if p.account.name == account
              and get_date(p) <= end_date
              and get_date(p) >= start_date]

        ps.sort(key=lambda p: get_date(p), reverse=True)
        subset = subset_sum([p.amount for p in ps], amnt)
        if not subset:
            return None
        else:
            return [ps[i] for i in subset]

    def to_excel(self, *,
                 destination: Path,
                 split_into_pairs: bool = False,
                 renumber: bool = False,
                 extra_columns: bool = False,
                 first_fiscal_month: int = 1,
                 opening_balance_date: date | None = None,
                 opening_balance_account: Account | None = None
                 ) -> None:
        # Create three polars DataFrames and save them as tables in an Excel file.
        acc_df = Account.to_dataframe(self.accounts)
        ps_df = Txn.to_dataframe(
            self.txns,
            renumber=renumber,
            split_into_pairs=split_into_pairs,
            extra_columns=extra_columns,
            first_fiscal_month=first_fiscal_month,
            opening_balance_date=opening_balance_date,
            opening_balance_account=opening_balance_account)
        bassertions_df = BAssertion.to_dataframe(self.bassertions)

        wb = xlsxwriter.Workbook(destination)
        acc_df.write_excel(
            workbook=wb,
            worksheet="Comptes",
            autofit=True,
            column_formats={"Numéro": "0"},
            table_name="Comptes",
            table_style="TableStyleMedium2",
            hide_gridlines= True)
        ps_df.write_excel(
            workbook=wb,
            worksheet="Txns",
            autofit=True,
            column_widths={"Commentaire": 350, "Autres comptes": 350, "Description du relevé": 350},
            column_formats={"No txn": "0", "Année fiscale": "0"},
            table_name="Txns",
            table_style="TableStyleMedium2",
            hide_gridlines=True)
        bassertions_df.write_excel(
            workbook=wb,
            worksheet="Soldes",
            autofit=True,
            column_widths={"Commentaire": 350},
            table_name="Soldes",
            table_style="TableStyleMedium2",
            hide_gridlines=True)
        wb.close()

    @classmethod
    def from_excel(cls, source: Path):
        acc_df = pl.read_excel(source, table_name="Comptes",
                               schema_overrides={
                                   'Compte': pl.String,
                                   'Type': pl.String,
                                   'Groupe': pl.String,
                                   'Sous-groupe': pl.String,
                                   'Numéro': pl.Int64
                               })
        accounts = Account.from_dataframe(acc_df)
        accounts_dict = {a.name: a for a in accounts}

        postings_df = pl.read_excel(
            source, table_name="Txns",
            schema_overrides={
                'No txn': pl.Int64,
                'Date': pl.Date,
                'Compte': pl.String,
                'Montant': pl.Float64,
                'Date du relevé': pl.Date,
                'Commentaire': pl.String,
                'Description du relevé': pl.String,
            })
        txns = Txn.from_dataframe(
            postings_df, accounts=accounts_dict)

        bassertions = pl.read_excel(
            source, table_name="Soldes",
            schema_overrides={
                'Date': pl.Date,
                'Compte': pl.String,
                'Solde': pl.Float64,
                'Commentaire': pl.String
            })
        bassertions = BAssertion.from_dataframe(
            bassertions, accounts=accounts_dict)

        return Journal(accounts=accounts, txns=txns, bassertions=bassertions)

def subset_sum(amounts: list[Decimal], target: Decimal) -> list[int]:
    """
    Finds a subset of the amounts that sum to the target amount.
    Amounts at the front of the list are preferred.

    Returns the positions of the subset in the original list
    or an empty list if no subset is found.
    """
    sum_dict: dict[Decimal, list[int]] = {}
    for i, p in enumerate(amounts):
        diff = target - p
        # Is p the target?
        if diff == Decimal(0):
            return [i]

        # Is there a diff in the dict that is the target?
        if diff in sum_dict:
            ls = sum_dict[diff]
            ls.append(i)
            return ls

        # Too bad, we have to add p to the dict
        for k, v in list(sum_dict.items()):  # Make a copy of the items because we mutate the dict
            new_sum = k + p
            if new_sum not in sum_dict:
                ls = v.copy()
                ls.append(i)
                sum_dict[new_sum] = ls
        if p not in sum_dict:
            sum_dict[p] = [i]
    return []
