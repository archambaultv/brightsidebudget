from collections import defaultdict
from decimal import Decimal
from datetime import date as date_type

from pydantic import BaseModel, Field, model_validator
import polars as pl

from brightsidebudget.txn.posting import Posting
from brightsidebudget.account.account import Account
from brightsidebudget.utils import fiscal_year


class Txn(BaseModel):
    

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

    def sort_key(self) -> tuple[date_type, int, int]:
        """
        Sort key for transactions.
        Sorts by date, then by the minimum account number, then by transaction ID.
        """
        return (self.date, min((p.account.number for p in self.postings)), self.txn_id)

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

    @staticmethod
    def to_dataframe(txns: list['Txn'],
                     renumber: bool = False,
                     first_fiscal_month: int = 1) -> pl.DataFrame:
        if renumber:
            txns = sorted(txns, key=lambda t: t.sort_key())
                
        ps = []
        for i, t in enumerate(txns):
            accs = sorted(t.accounts(), key=lambda a: a.sort_key())
            accs = [a.name for a in accs]
            for p in t.postings:
                other_accounts = [a for a in accs if a != p.account.name]
                p_dict = p.model_dump()
                if renumber:
                    p_dict["txn_id"] = i + 1
                p_dict["account"] = p_dict["account"]["name"]
                p_dict["Autres comptes"] = " | ".join(other_accounts)
                p_dict["Année fiscale"] = fiscal_year(p.date, first_fiscal_month)
                ps.append(p_dict)
        return pl.DataFrame(ps).rename(
            {
                'txn_id': 'No txn',
                'date': 'Date',
                'account': 'Compte',
                'amount': 'Montant',
                'comment': 'Commentaire',
                'stmt_date': 'Date du relevé',
                'stmt_desc': 'Description du relevé'
            }
        )

    @staticmethod
    def from_dataframe(df: pl.DataFrame, accounts: dict[str, Account]) -> list['Txn']:
        """
        Convert a DataFrame to a list of Txn objects.
        """
        postings = []
        for row in df.to_dicts():
            p = Posting(
                txn_id=row['No txn'],
                date=row['Date'],
                account=accounts[row['Compte']],
                amount=row['Montant'],
                comment=row["Commentaire"] if row["Commentaire"] else "",
                stmt_date=row["Date du relevé"] if row["Date du relevé"] else None, # type: ignore
                stmt_desc= row["Description du relevé"] if row["Description du relevé"] else ""
            )
            postings.append(p)

        return Txn.from_postings(postings)

