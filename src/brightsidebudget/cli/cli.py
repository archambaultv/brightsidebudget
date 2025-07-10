import click

from brightsidebudget.cli.check_command import check_command
from brightsidebudget.cli.import_command import import_txns_command
from brightsidebudget.cli.export_command import export_command
from brightsidebudget.cli.rewrite_command import rewrite_command


@click.group(help="bsb — Bright Side Budget CLI")
def cli():
    """
    Point d'entrée principal pour la CLI de Bright Side Budget.
    """
    pass

# Ajout des commandes à la CLI
cli.add_command(check_command)
cli.add_command(export_command)
cli.add_command(rewrite_command)
cli.add_command(import_txns_command)

def main():
    """
    Point d'entrée principal pour le package Bright Side Budget.
    """
    cli()
