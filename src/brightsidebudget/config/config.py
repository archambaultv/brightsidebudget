from pathlib import Path
from pydantic import BaseModel, ConfigDict

from brightsidebudget.journal import Journal
from brightsidebudget.config.export_config import ExportConfig
from brightsidebudget.config.import_config import ImportConfig
from brightsidebudget.config.check_config import CheckConfig
from brightsidebudget.config.rewrite_config import RewriteConfig

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
                for n in self.check_config.forbidden_accounts_for_txns:
                    if n not in [a.name for a in journal.accounts]:
                        raise ValueError(f"Forbidden account not found in journal: {n}")
                for txn in journal.txns:
                    for posting in txn.postings:
                        if posting.account.name in self.check_config.forbidden_accounts_for_txns:
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
        for import_conf in config.import_config.importation:
            if not import_conf.import_folder.is_absolute():
                import_conf = import_conf.model_copy(update={
                    "import_folder": config_path.parent / import_conf.import_folder
                })
            if not import_conf.rules.file.is_absolute():
                import_conf = import_conf.model_copy(update={
                    "rules": import_conf.rules.model_copy(update={
                        "file": config_path.parent / import_conf.rules.file
                    })
                })

        return config