from datetime import date as date_type
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, model_validator
from brightsidebudget.account.account import Account


class Posting(BaseModel):
    
    txn_id: int = Field(..., ge=0, description="Transaction ID, must be a positive integer")
    date: date_type = Field(..., description="Date of the transaction")
    account: Account = Field(..., description="Account associated with the transaction")
    amount: Decimal = Field(..., description="Amount of the transaction")
    comment: str = Field(default="", description="Comment for the transaction")
    stmt_date: date_type = Field(default=None, description="Statement date, defaults to transaction date if not provided") # type: ignore
    stmt_desc: str = Field(default="", description="Description from the statement, defaults to empty string")

    @model_validator(mode="before")
    @classmethod
    def stmt_date_none(cls, data: Any):
        if "stmt_date" not in data or data["stmt_date"] is None:
            # If stmt_date is not provided, set it to the transaction date
            data["stmt_date"] = data["date"]
        return data
    
    def __str__(self) -> str:
        s = f"Posting(id={self.txn_id}, date={self.date}, account={self.account.name}, amount={self.amount}, stmt_desc={self.stmt_desc})"
        return s

    def __repr__(self) -> str:
        return self.__str__()

    def dedup_key(self) -> tuple[date_type, str, Decimal, str]:
        return self.date, self.account.name, self.amount, self.stmt_desc

    def sort_key(self) -> tuple[date_type, int, int]:
        """
        Sort key for postings.
        Sorts by date, then by account number, then by transaction ID.
        """
        return self.date, self.account.number, self.txn_id
