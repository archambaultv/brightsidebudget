from pathlib import Path
from typing import Protocol
import json
import logging

from pydantic import BaseModel

from brightsidebudget.account.account import Account
from brightsidebudget.bank_import.import_rule import Rule
from brightsidebudget.txn.posting import Posting
from brightsidebudget.txn.txn import Txn


class IClassifier(Protocol):
    def classify(self, *, posting: Posting) -> Txn | list[Txn] | None:
        ...

class RuleClassifier(BaseModel):
    """
    Classifier that uses rules to classify postings into transactions.
    """
    model_config = {
        "arbitrary_types_allowed": True,
    }
    file: Path
    accounts: dict[str, Account]
    logger: logging.Logger
    _rules = []

    def classify(self, *, posting: Posting) -> Txn | list[Txn] | None:
        """Classify a posting using the defined rules."""
        if not self._rules:
            self._rules = self.load_rules()
        for rule in self._rules:
            if rule.match(posting):
                txns = rule.make_txns(posting, self.accounts)
                self.logger.info(f"Posting {posting} classified by rule: {rule}")
                return txns
        
        raise ValueError(f"No rule matched for posting: {posting}")

    def load_rules(self) -> list[Rule]:
        """
        Load classification rules from the specified json file.
        """
        with open(self.file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [Rule(**rule) for rule in data]