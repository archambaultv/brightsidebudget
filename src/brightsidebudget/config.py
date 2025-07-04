from pathlib import Path
from pydantic import BaseModel

from brightsidebudget.journal.journal import Journal
from brightsidebudget.journal.journal_repository import ExcelJournalRepository


class Config(BaseModel):
    

    journal_path: Path
    backup_dir: Path
    verify_no_uncategorized_txns: bool = True
    verify_balance_assertions: bool = True
    auto_stmt_date: list[str] = []
    auto_balance: dict[str, str] = {}
    auto_balance_assertion: dict[str, float] = {}
    importation: list[dict] = []


    def get_journal(self, skip_check: bool = False) -> Journal:
        """
        Get the path to the journal file.
        """
        if not self.journal_path.exists():
            raise FileNotFoundError(f"Journal file not found: {self.journal_path}")

        if self.journal_path.suffix.lower() == '.xlsx':
            repo = ExcelJournalRepository()
        else:
            raise ValueError(f"Unsupported journal file format: {self.journal_path}")
        journal = repo.get_journal(self.journal_path)

        if not skip_check:
            if self.verify_no_uncategorized_txns:
                uncat = [t for t in journal.txns if t.is_uncategorized()]
                if uncat:
                    ids = ', '.join(str(t.txn_id) for t in uncat)
                    raise ValueError("Journal contains uncategorized transactions. "
                                    f"Transaction IDs: {ids}")

            if self.verify_balance_assertions:
                unbal = journal.failed_bassertions()
                if unbal:
                    ids = ', '.join(str(b.dedup_key()) for b in unbal)
                    raise ValueError("Journal contains balance assertions that do not balance. "
                                    f"Assertion keys: {ids}")
        
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

        return config