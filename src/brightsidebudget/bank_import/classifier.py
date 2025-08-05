from pathlib import Path
from typing import Protocol
import json
import logging

from pydantic import BaseModel

from brightsidebudget.account.account import Account
from brightsidebudget.bank_import.import_rule import Rule
from brightsidebudget.bank_import.newtxn import NewTxn
from brightsidebudget.txn.posting import Posting
from brightsidebudget.txn.txn import Txn


class IClassifier(Protocol):
    def classify(self, *, posting: Posting) -> NewTxn | list[NewTxn] | None:
        ...

class RuleClassifier(BaseModel):
    """
    Classifier that uses rules to classify postings into transactions.
    """
    model_config = {
        "arbitrary_types_allowed": True,
    }
    file: Path
    default_account: str
    accounts: dict[str, Account]
    logger: logging.Logger
    _rules = []

    def classify(self, *, posting: Posting) -> NewTxn | list[NewTxn] | None:
        """Classify a posting using the defined rules."""
        if not self._rules:
            self._rules = self.load_rules()
        for rule in self._rules:
            if rule.match(posting):
                txns = rule.make_txns(posting, self.accounts)
                self.logger.info(f"Posting {posting} classified by rule: {rule}")
                if txns:
                    newtxns = []
                    for txn in txns:
                        newtxns.append(NewTxn(txn=txn, unmatched=False))
                else:
                    newtxns = None
                return newtxns
        self.logger.warning(f"No rule matched for posting: {posting}")
        a2 = self.accounts[self.default_account]
        p2 = posting.model_copy(update={"account": a2, "amount": -posting.amount})
        return NewTxn(txn=Txn(postings=[posting, p2]), unmatched=True)

    def load_rules(self) -> list[Rule]:
        """
        Load classification rules from the specified json file.
        """
        with open(self.file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [Rule(**rule) for rule in data]