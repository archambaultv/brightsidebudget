from collections import defaultdict
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from brightsidebudget.txn.posting import Posting
from brightsidebudget.account.account import Account


class Txn(BaseModel):
    model_config = ConfigDict(frozen=True)

    postings : list[Posting] = Field(..., min_length=2, description="List of postings in the transaction")
    
    @property
    def txn_id(self):
        return self.postings[0].txn_id

    @property
    def date(self):
        return self.postings[0].date

    def accounts(self) -> list[Account]:
        return sorted({p.account for p in self.postings}, key=lambda a: a.sort_key()) # type: ignore

    def is_uncategorized(self) -> bool:
        return any(p.account.type.name == "Non classé" for p in self.postings)

    @staticmethod
    def from_postings(ps: list['Posting']) -> list['Txn']:
        d: dict[int, list[Posting]] = defaultdict(list)
        for p in ps:
            d[p.txn_id].append(p)
        return sorted((Txn(postings=v) for v in d.values()), key=lambda t: t.txn_id)

    @model_validator(mode="after")
    def validate_txn(self):

        s_txnid = set(p.txn_id for p in self.postings)
        if len(s_txnid) != 1:
            raise ValueError(f"Txn has different txn_ids : {s_txnid}")

        s_date = set(p.date for p in self.postings)
        if len(set(s_date)) != 1:
            raise ValueError(f"Txn {self.txn_id} has different dates : {s_date}")

        s = sum((p.amount for p in self.postings), start=Decimal(0))
        if s != Decimal(0):
            raise ValueError(f"Txn {self.txn_id} does not balance. Total: {s}")

        return self
