from datetime import date as date_type
from decimal import Decimal
from functools import reduce
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator
from brightsidebudget.account.account import Account


class Posting(BaseModel):
    model_config = ConfigDict(frozen=True)
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
        s = f"{self.txn_id} {self.date} {self.account} {self.amount}"
        if self.stmt_desc:
            return f"{s} {self.stmt_desc}"
        return s

    def __repr__(self) -> str:
        return self.__str__()

    def to_dict(self) -> dict[str, str]:
        return {"No txn": str(self.txn_id), "Date": str(self.date), "Compte": self.account.name,
                "Montant": str(self.amount), "Commentaire": self.comment,
                "Date du relevé": str(self.stmt_date),
                "Description du relevé": self.stmt_desc}

    @classmethod
    def from_dict(cls, row: dict[str, str], accounts: dict[str, Account]) -> 'Posting':
        acc = accounts[row["Compte"]]

        return cls(txn_id=row["No txn"], date=row["Date"], # type: ignore
                   account=acc, amount=row["Montant"], # type: ignore
                   comment=row["Commentaire"],
                   stmt_date=row.get("Date du relevé", None), # type: ignore
                   stmt_desc=row["Description du relevé"])

    def dedup_key(self) -> tuple[date_type, str, Decimal, str]:
        return self.date, self.account.name, self.amount, self.stmt_desc

    def sort_key(self) -> tuple[date_type, int, int]:
        return self.date, self.txn_id, self.account.number

    @staticmethod
    def renumber(postings: list['Posting']) -> list['Posting']:
        """
        Renumber postings in the list by filling gaps in transaction IDs
        and ensuring they are sequential starting from 1.
        """
        if not postings:
            return []

        def foo(acc: tuple[list['Posting'], int], posting: 'Posting') -> tuple[list['Posting'], int]:
            new_ps, last_txn_id = acc
            
            if posting.txn_id != last_txn_id:
                new_id = new_ps[-1].txn_id + 1
            else:
                new_id = new_ps[-1].txn_id
            
            new_posting = posting.model_copy(update={"txn_id": new_id})
            new_ps.append(new_posting)
            
            return new_ps, posting.txn_id
        
        # Initialize with first posting
        ps = sorted(postings, key=lambda p: p.txn_id)
        first_posting = ps[0].model_copy(update={"txn_id": 1})
        initial_acc = ([first_posting], ps[0].txn_id)
        
        # Process remaining postings
        final_acc, _ = reduce(foo, ps[1:], initial_acc)
        
        return final_acc