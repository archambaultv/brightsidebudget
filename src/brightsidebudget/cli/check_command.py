from pathlib import Path

import click

from brightsidebudget.config import Config


@click.command(
    name="check",
    help=(
        "Vérifie la validité du journal."
    )
)
@click.argument(
    "config_path",
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    required=True
)

def check_command(config_path: Path):
    """
    Vérifie la validité du journal.
    """
    config = Config.from_user_config(config_path)
    config.get_journal()
    print("Le journal est valide. Aucune erreur détectée.")
