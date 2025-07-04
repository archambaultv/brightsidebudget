from pathlib import Path
from pydantic import BaseModel, ConfigDict

from brightsidebudget.journal.journal import Journal
from brightsidebudget.journal.journal_repository import ExcelJournalRepository


class Config(BaseModel):
    model_config = ConfigDict(frozen=True)

    journal_path: Path
    verify_no_uncategorized_txns: bool = True
    verify_balance_assertions: bool = True


    def get_journal(self) -> Journal:
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
        
        config = cls.model_validate_json(config_path.read_text())
        if not config.journal_path.is_absolute():
            config = config.model_copy(update={
                "journal_path": config_path.parent / config.journal_path
            })

        return config