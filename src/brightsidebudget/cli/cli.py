import click

from brightsidebudget.cli.check import check_command


@click.group(help="bsb — Bright Side Budget CLI")
def cli():
    """
    Point d'entrée principal pour la CLI de Bright Side Budget.
    """
    pass

# Ajout des commandes à la CLI
cli.add_command(check_command)

def main():
    """
    Point d'entrée principal pour le package Bright Side Budget.
    """
    cli()
