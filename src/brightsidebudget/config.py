from datetime import date
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field

from brightsidebudget.journal import Journal

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

class ImportConfig(BaseModel):
    """
    Configuration for importing transactions into the journal.
    """
    auto_stmt_date: list[str] = []
    auto_balance: dict[str, str] = {}
    auto_balance_assertion: dict[str, float] = {}
    importation: list[dict] = []

class CheckConfig(BaseModel):
    """
    Configuration for checking the journal.
    """
    model_config = ConfigDict(extra="forbid")

    forbidden_accounts_for_txns: list[str] = []
    verify_balance_assertions: bool = True

class RewriteConfig(BaseModel):
    """
    Configuration for rewriting the journal.
    """
    model_config = ConfigDict(extra="forbid")

    split_into_pairs: bool = False
    renumber: bool = False

class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    journal_path: Path
    backup_dir: Path = Path("Sauvegardes")
    log_dir: Path = Path("Logs")

    check_config: CheckConfig
    export_config: ExportConfig
    import_config: ImportConfig
    rewrite_config: RewriteConfig

    def get_journal(self, skip_check: bool = False) -> Journal:
        """
        Get the path to the journal file.
        """
        if not self.journal_path.exists():
            raise FileNotFoundError(f"Journal file not found: {self.journal_path}")

        if not self.journal_path.suffix.lower() == '.xlsx':
            raise ValueError(f"Unsupported journal file format: {self.journal_path}")
        journal = Journal.from_excel(self.journal_path)

        if not skip_check:
            if self.check_config.forbidden_accounts_for_txns:
                forbidden_txns = []
                for txn in journal.txns:
                    for posting in txn.postings:
                        if posting.account.type.name in self.check_config.forbidden_accounts_for_txns:
                            forbidden_txns.append(txn)
                            break
                if forbidden_txns:
                    ids = ', '.join(str(t.txn_id) for t in forbidden_txns)
                    raise ValueError("Journal contains transactions with forbidden accounts: " +
                                    f"Transaction IDs: {ids}")

            if self.check_config.verify_balance_assertions:
                unbal = journal.failed_bassertions()
                if unbal:
                    msg = "Journal contains balance assertions that do not balance."
                    for bassertion in unbal:
                        actual = journal.account_balance(bassertion.account.name, bassertion.date,
                                                         use_stmt_date=True)
                        msg += f"\n  - {bassertion.date} {bassertion.account.name}"
                        msg += f" expected {bassertion.balance}, " \
                               f"found {actual}" \
                               f" (difference: {bassertion.balance - actual})"
                    raise ValueError(msg)
        
        return journal

    @classmethod
    def from_user_config(cls, config_path: Path) -> 'Config':
        """
        Load configuration from a user-defined JSON file.
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        config = cls.model_validate_json(config_path.read_text(encoding='utf-8'))
        if not config.journal_path.is_absolute():
            config = config.model_copy(update={
                "journal_path": config_path.parent / config.journal_path
            })
        if not config.backup_dir.is_absolute():
            config = config.model_copy(update={
                "backup_dir": config_path.parent / config.backup_dir
            })
        if not config.log_dir.is_absolute():
            config = config.model_copy(update={
                "log_dir": config_path.parent / config.log_dir
            })

        return config