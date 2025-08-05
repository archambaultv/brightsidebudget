from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field

class BankCsvConfig(BaseModel):
    """
    Configuration for importing transactions into a specific account.
    """
    model_config = ConfigDict(extra="forbid")

    date_col: str = Field(..., min_length=1)
    stmt_desc_cols: list[str] = []
    stmt_date_col: str = ""
    amount_col: str = ""
    amount_in_col: str = ""
    amount_out_col: str = ""
    encoding: str = "utf8"
    csv_delimiter: str = ","
    remove_delimiter_from: list[str] = []
    skiprows: int = 0

class RulesConfig(BaseModel):
    """
    Configuration for rules applied during import.
    """
    model_config = ConfigDict(extra="forbid")

    file: Path
    default_account: str

class AccountImportConfig(BaseModel):
    """
    Configuration for importing transactions into a specific account.
    """
    model_config = ConfigDict(extra="forbid")

    account: str
    import_folder: Path
    bank_csv: BankCsvConfig
    rules: RulesConfig

class ImportConfig(BaseModel):
    """
    Configuration for importing transactions into the journal.
    """
    model_config = ConfigDict(extra="forbid")

    auto_stmt_date: list[str] = []
    auto_balance: dict[str, str] = {}
    auto_balance_assertion: dict[str, float] = {}
    importation: list[AccountImportConfig] = []
    export_after_import: bool = True