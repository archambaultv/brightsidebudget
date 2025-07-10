from pathlib import Path

import click

from brightsidebudget.config import Config
from brightsidebudget.journal import Journal


@click.command(
    name="export",
    help=(
        "Exporte le journal au format Excel avec des colonnes supplémentaires pour les transactions"
    )
)
@click.argument(
    "config_path",
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    required=True
)

def export_command(config_path: Path):
    """
    Exporte le journal au format Excel avec des colonnes supplémentaires pour les transactions.
    """
    config = Config.from_user_config(config_path)
    journal =config.get_journal()
    export_journal(config, journal)


def export_journal(config: Config, journal: Journal):
    opening_balance_account = None
    if config.export_config.opening_balance_account:
        opening_balance_account = journal.get_account(config.export_config.opening_balance_account)
    journal.to_excel(destination=config.export_config.export_path,
                     renumber=config.export_config.renumber,
                     split_into_pairs=config.export_config.split_into_pairs,
                     extra_columns=True,
                     first_fiscal_month=config.export_config.first_fiscal_month,
                     opening_balance_date=config.export_config.opening_balance_date,
                     opening_balance_account=opening_balance_account)
    print("Le journal a été exporté avec succès.")
