from typing import Protocol

from brightsidebudget.txn.posting import Posting
from brightsidebudget.txn.txn import Txn


class IClassifier(Protocol):
    def classify(self, *, posting: Posting) -> Txn | list[Txn] | None:
        ...