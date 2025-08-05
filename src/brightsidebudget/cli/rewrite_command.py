from datetime import datetime
from pathlib import Path
import shutil

import click

from brightsidebudget.config.config import Config


@click.command(
    name="rewrite",
    help=(
        "Rewrite journal based on the rewrite configuration."
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

def rewrite_command(config_path: Path, dry_run: bool = False):
    """
    Importe de nouvelles transactions dans le journal à partir du fichier de configuration.
    """
    config = Config.from_user_config(config_path)
    journal = config.get_journal()

    # Backup journal before importing
    now = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
    backup_name = f"{config.journal_path.stem}-{now}.xlsx"
    shutil.copy(config.journal_path, config.backup_dir / backup_name)

    # Save the journal after import
    journal.to_excel(destination=config.journal_path,
                     extra_columns=False,
                     renumber=config.rewrite_config.renumber,
                     split_into_pairs=config.rewrite_config.split_into_pairs)
