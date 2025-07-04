from decimal import Decimal
from pydantic import BaseModel, Field

from brightsidebudget.account.account import Account
from brightsidebudget.txn.posting import Posting
from brightsidebudget.txn.txn import Txn


class Rule(BaseModel):
    """
    A rule for classifying postings into transactions.
    Each rule is a callable that takes a Posting and returns a Txn or None.
    """
    account_name: str | None = None
    description_startswith: str | None = None
    description_equals: list[str] | None = None
    amount_equals: Decimal | None = None
    amount_greater_than: Decimal | None = None
    amount_less_than: Decimal | None = None

    second_account_name: str | None = Field(default=None, min_length=1)
    discard: bool = False
    second_txn: dict | None = None

    def match(self, posting: Posting) -> bool:
        """
        Check if the posting matches the rule.
        """
        if self.description_startswith and not posting.stmt_desc.startswith(self.description_startswith):
            return False
        if self.description_equals and posting.stmt_desc not in self.description_equals:
            return False
        if self.amount_equals is not None and posting.amount != self.amount_equals:
            return False
        if self.amount_greater_than is not None and posting.amount <= self.amount_greater_than:
            return False
        if self.amount_less_than is not None and posting.amount >= self.amount_less_than:
            return False
        if self.account_name and posting.account.name != self.account_name:
            return False
        
        return True

    def get_txns(self, posting: Posting, accounts: dict[str, Account]) -> list[Txn] | None:
        """
        Create transactions based on the rule and the given posting.
        """
        if self.discard:
            return None

        if self.second_account_name is None:
            raise ValueError("Second account name must be provided if discard is False.")
        txns = []
        a2 = accounts[self.second_account_name]
        p2 = posting.model_copy(update={"account": a2, "amount": -posting.amount})
        txns.append(Txn(postings=[posting, p2]))

        if self.second_txn:
            # Create a second transaction if specified
            txn_id = posting.txn_id + 1
            a1 = accounts[self.second_txn["account1"]]
            a2 = accounts[self.second_txn["account2"]]
            amnt = self.second_txn["amount1"]
            p1 = posting.model_copy(update={"txn_id": txn_id, "account": a1, "amount": amnt})
            p2 = posting.model_copy(update={"txn_id": txn_id, "account": a2, "amount": -amnt})
            txns.append(Txn(postings=[p1, p2]))

        return txns