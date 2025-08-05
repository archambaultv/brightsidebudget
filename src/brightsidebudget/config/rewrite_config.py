from pydantic import BaseModel, ConfigDict


class RewriteConfig(BaseModel):
    """
    Configuration for rewriting the journal.
    """
    model_config = ConfigDict(extra="forbid")

    split_into_pairs: bool = False
    renumber: bool = False