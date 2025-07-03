from datetime import date as date_type
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from brightsidebudget.account.account import Account


class BAssertion(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: date_type
    account: Account
    balance: Decimal
    comment: str = Field(default="")

    def to_dict(self) -> dict[str, str]:
        return {"Date": str(self.date), "Compte": self.account.name, "Solde": str(self.balance),
                "Commentaire": self.comment}

    @classmethod
    def from_dict(cls, row: dict[str, str], accounts: dict[str, Account]) -> 'BAssertion':
        acc = accounts[row["Compte"]]
        return cls(date=row["Date"], account=acc, balance=row["Solde"], # type: ignore
                   comment=row["Commentaire"])

    def dedup_key(self) -> tuple[date_type, str]:
        return self.date, self.account.name

    def sort_key(self) -> tuple[date_type, int]:
        return self.date, self.account.number
