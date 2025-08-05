from pydantic import BaseModel, ConfigDict

from brightsidebudget.txn.txn import Txn

class NewTxn(BaseModel):
    """
    A new transaction to be added to the journal.
    """
    model_config = ConfigDict(extra="forbid")

    txn: Txn
    unmatched: bool