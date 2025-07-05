from datetime import date
from pydantic import BaseModel
from brightsidebudget.txn.posting import Posting
from brightsidebudget.txn.txn import Txn


class PostingExtra(BaseModel):
    """
    A class to represent additional information for a posting.
    This is used to store extra data that is not part of the standard posting fields.
    """
    posting: Posting
    fiscal_year: int
    other_accounts: list[str]

    @staticmethod
    def from_txns(txns: list[Txn], first_fiscal_month = 1) -> list['PostingExtra']:
        """
        Create a list of PostingExtra from a list of transactions.
        """
        ps_extra = []
        for txn in txns:
            accs = sorted(txn.accounts(), key=lambda a: a.sort_key())
            accs = [a.name for a in accs]
            for p in txn.postings:
                other_accs = [a for a in accs if a != p.account.name]
                ps_extra.append(
                    PostingExtra(
                        posting=p,
                        fiscal_year=fiscal_year(p.date, first_fiscal_month),
                        other_accounts=other_accs
                    )
                )
        return ps_extra

def fiscal_year(date: date, first_fiscal_month: int = 1) -> int:
    """
    Calculate the fiscal year for a given date.
    """
    if first_fiscal_month == 1 or date.month < first_fiscal_month:
        return date.year
    else:
        return date.year + 1