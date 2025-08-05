from pydantic import BaseModel, ConfigDict


class CheckConfig(BaseModel):
    """
    Configuration for checking the journal.
    """
    model_config = ConfigDict(extra="forbid")

    forbidden_accounts_for_txns: list[str] = []
    verify_balance_assertions: bool = True