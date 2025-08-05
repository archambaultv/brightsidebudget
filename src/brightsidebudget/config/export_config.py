from datetime import date
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field


class ExportConfig(BaseModel):
    """
    Configuration for exporting the journal.
    """
    model_config = ConfigDict(extra="forbid")

    export_path: Path
    first_fiscal_month: int = Field(ge=1, le=12, default=1)
    split_into_pairs: bool = False
    renumber: bool = False
    opening_balance_date: date | None = None
    opening_balance_account: str | None = None