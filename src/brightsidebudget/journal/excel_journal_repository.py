from pathlib import Path

import xlsxwriter
import polars as pl

from brightsidebudget.account.account import Account
from brightsidebudget.bassertion.bassertion import BAssertion
from brightsidebudget.journal.journal import Journal
from brightsidebudget.txn.txn import Txn

ACCOUNT_HEADER : list[str] = ["Compte", "Type", "Groupe", "Sous-groupe", "Numéro"]
POSTING_HEADER = ["No txn", "Date", "Compte", "Montant", "Date du relevé", "Commentaire",
          "Description du relevé"]

POSTING_EXTRA_HEADER = ["Autres comptes", "Année fiscale"]
BASSERTION_HEADER = ["Date", "Compte", "Solde", "Commentaire"]

class ExcelJournalRepository():
    """
    Journal repository for Excel files.
    Reads or creates a single workbook with three sheets:
      - Comptes
      - Txns
      - Soldes
    """
    def write_journal(self, *, journal: Journal,
                      destination: Path,
                      renumber: bool = False,
                      first_fiscal_month: int = 1) -> None:
        # Create three polars DataFrames and save them as tables in an Excel file.
        acc_df = Account.to_dataframe(journal.accounts)
        ps_df = Txn.to_dataframe(
            journal.txns,
            renumber=renumber,
            first_fiscal_month=first_fiscal_month)
        bassertions_df = BAssertion.to_dataframe(journal.bassertions)

        wb = xlsxwriter.Workbook(destination)
        acc_df.write_excel(
            workbook=wb,
            worksheet="Comptes",
            table_name="Comptes",
            table_style="TableStyleMedium2",
            hide_gridlines= True)
        ps_df.write_excel(
            workbook=wb,
            worksheet="Txns",
            table_name="Txns",
            table_style="TableStyleMedium2",
            hide_gridlines=True)
        bassertions_df.write_excel(
            workbook=wb,
            worksheet="Soldes",
            table_name="Soldes",
            table_style="TableStyleMedium2",
            hide_gridlines=True)
        wb.close()

    def read_journal(self, source: Path) -> Journal:
        acc_df = pl.read_excel(source, table_name="Comptes",
                               schema_overrides={
                                   'Compte': pl.String,
                                   'Type': pl.String,
                                   'Groupe': pl.String,
                                   'Sous-groupe': pl.String,
                                   'Numéro': pl.Int64
                               })
        accounts = Account.from_dataframe(acc_df)
        accounts_dict = {a.name: a for a in accounts}

        postings_df = pl.read_excel(
            source, table_name="Txns",
            schema_overrides={
                'No txn': pl.Int64,
                'Date': pl.Date,
                'Compte': pl.String,
                'Montant': pl.Float64,
                'Date du relevé': pl.Date,
                'Commentaire': pl.String,
                'Description du relevé': pl.String,
            })
        txns = Txn.from_dataframe(
            postings_df, accounts=accounts_dict)

        bassertions = pl.read_excel(
            source, table_name="Soldes",
            schema_overrides={
                'Date': pl.Date,
                'Compte': pl.String,
                'Solde': pl.Float64,
                'Commentaire': pl.String
            })
        bassertions = BAssertion.from_dataframe(
            bassertions, accounts=accounts_dict)

        return Journal(accounts=accounts, txns=txns, bassertions=bassertions)
