from datetime import datetime
from pathlib import Path
import shutil
import logging

import click

from brightsidebudget.bank_import.import_service import ImportService
from brightsidebudget.config import Config
from brightsidebudget.journal.excel_journal_repository import ExcelJournalRepository


def setup_logging(config: Config) -> logging.Logger:
    """Setup logging for the import process."""
    # Create log directory if it doesn't exist
    config.log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log filename with timestamp
    now = datetime.now().strftime("%Y-%m-%d-%Hh-%Mm-%Ss")
    log_filename = f"bsb-import-{now}.log"
    log_path = config.log_dir / log_filename
    
    # Configure logger
    logger = logging.getLogger("bsb_import")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create file handler
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    
    return logger


@click.command(
    name="import",
    help=(
        "Importe de nouvelles transactions"
    )
)
@click.argument(
    "config_path",
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    required=True
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Effectue une simulation de l'importation sans enregistrer les modifications."
)

def import_txns_command(config_path: Path, dry_run: bool = False):
    """
    Génère la grille d'évaluation à présenter aux élèves à partir du fichier de configuration.
    """
    config = Config.from_user_config(config_path)
    logger = setup_logging(config)
    
    logger.info("=== BrightSide Budget Import Started ===")
    logger.info(f"Config file: '{config_path}'")
    logger.info(f"Journal file: '{config.journal_path}'")
    logger.info(f"Dry run mode: {dry_run}")

    if dry_run:
        msg = "Exécution en mode simulation. Aucune modification ne sera enregistrée."
        print(msg)

    importer = ImportService(config=config, logger=logger)
    journal = importer.load_and_update_journal()
    if not dry_run:
        # Backup journal before importing
        now = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
        backup_name = f"{config.journal_path.stem}-{now}.xlsx"
        shutil.copy(config.journal_path, config.backup_dir / backup_name)

        # Save the journal after import
        repo = ExcelJournalRepository()
        repo.write_journal(journal=journal, destination=config.journal_path)
    msg = f"Importation terminée{' (dry-run)' if dry_run else ''}."
    logger.info(msg)
    print(msg)
