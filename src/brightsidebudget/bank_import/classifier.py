from decimal import Decimal
from pathlib import Path
from typing import Protocol
import json

from pydantic import BaseModel, Field

from brightsidebudget.account.account import Account
from brightsidebudget.txn.posting import Posting
from brightsidebudget.txn.txn import Txn


class IClassifier(Protocol):
    def classify(self, *, posting: Posting) -> Txn | list[Txn] | None:
        ...

class Rule(BaseModel):
    """
    A rule for classifying postings into transactions.
    Each rule is a callable that takes a Posting and returns a Txn or None.
    """
    description_startswith: str | None = None
    description_equals: str | None = None
    amount_equals: Decimal | None = None
    amount_greater_than: Decimal | None = None
    amount_less_than: Decimal | None = None
    account_name: str | None = None

    second_account_name: str = Field(..., min_length=1)
    discard: bool = False
    second_txn: dict | None = None

    def match(self, posting: Posting, accounts: dict[str, Account]) -> Txn | None:
        """
        Check if the posting matches the rule.
        If it does, return a Txn; otherwise, return None.
        """
        if self.description_startswith and not posting.stmt_desc.startswith(self.description_startswith):
            return None
        if self.description_equals and posting.stmt_desc != self.description_equals:
            return None
        if self.amount_equals is not None and posting.amount != self.amount_equals:
            return None
        if self.amount_greater_than is not None and posting.amount <= self.amount_greater_than:
            return None
        if self.amount_less_than is not None and posting.amount >= self.amount_less_than:
            return None
        if self.account_name and posting.account.name != self.account_name:
            return None
        
        # If all checks passed, create a Txn with the posting or return None if discard is True
        if self.discard:
            return None

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

        return Txn(postings=[posting, p2])

class RuleClassifier(BaseModel, IClassifier):
    """
    Classifier that uses rules to classify postings into transactions.
    """
    rules: Path
    default_account: str = Field(..., min_length=1)
    accounts: dict[str, Account]

    def classify(self, *, posting: Posting) -> Txn | list[Txn] | None:
        """Classify a posting using the defined rules."""
        rules = self.load_rules()
        for rule in rules:
            txn = rule.match(posting, self.accounts)
            if txn:
                return txn
        
        a2 = self.accounts[self.default_account]
        p2 = posting.model_copy(update={"account": a2, "amount": -posting.amount})
        return Txn(postings=[posting, p2])

    def load_rules(self) -> list[Rule]:
        """
        Load classification rules from the specified json file.
        """
        with open(self.rules, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [Rule(**rule) for rule in data]