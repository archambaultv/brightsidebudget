from datetime import date as date_type
from decimal import Decimal

from pydantic import BaseModel, Field
import polars as pl

from brightsidebudget.account.account import Account


class BAssertion(BaseModel):
    

    date: date_type
    account: Account
    balance: Decimal
    comment: str = Field(default="")

    def dedup_key(self) -> tuple[date_type, str]:
        return self.date, self.account.name

    def sort_key(self) -> tuple[date_type, int]:
        return self.date, self.account.number

    @staticmethod
    def to_dataframe(bassertions: list['BAssertion']) -> pl.DataFrame:
        xs = [b.model_dump(warnings=False) for b in bassertions]
        for x in xs:
            x['account'] = x['account']["name"]
        return pl.DataFrame(xs).rename(
            {
                'date': 'Date',
                'account': 'Compte',
                'balance': 'Solde',
                'comment': 'Commentaire'
            }
        )

    @staticmethod
    def from_dataframe(df: pl.DataFrame, accounts: dict[str, Account]) -> list['BAssertion']:
        bassertions = []
        for row in df.to_dicts():
            bassertion = BAssertion(
                date=row['Date'],
                account=accounts[row['Compte']],
                balance=row['Solde'],
                comment=row['Commentaire'] if row['Commentaire'] else ""
            )
            bassertions.append(bassertion)
        return bassertions