from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
import shutil

import click
from dateutil.relativedelta import relativedelta

from brightsidebudget.account.account import Account
from brightsidebudget.bank_import.bank_import import BankCsv
from brightsidebudget.bank_import.classifier import RuleClassifier
from brightsidebudget.bassertion.bassertion import BAssertion
from brightsidebudget.config import Config
from brightsidebudget.journal.journal import Journal
from brightsidebudget.journal.excel_journal_repository import ExcelJournalRepository
from brightsidebudget.txn.posting import Posting
from brightsidebudget.txn.txn import Txn


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
    journal = config.get_journal(skip_check=True)
    if dry_run:
        print("Exécution en mode simulation. Aucune modification ne sera enregistrée.")
    auto_update_journal(journal, config)
    import_new_txns(journal, config)
    if not dry_run:
        # Save the journal after import
        repo = ExcelJournalRepository()
        repo.write_journal(journal=journal, destination=config.journal_path)
    print("Importation terminée.")


def import_new_txns(journal: Journal, config: Config):
    """
    Imports new transactions into the journal based on the configuration.
    """
    if not config.importation:
        return

    # Backup journal before importing
    now = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
    backup_name = f"{config.journal_path.stem}-{now}.xlsx"
    shutil.copy(config.journal_path, config.backup_dir / backup_name)

    for import_conf in config.importation:
        # Create classifier
        acc = journal.get_account(import_conf["account"])
        acc_dict = {a.name: a for a in journal.accounts}
        classifier = RuleClassifier(
            file=import_conf["rules"]["file"],
            accounts=acc_dict
        )
        # Check import folder
        import_folder = Path(import_conf["import_folder"])
        if not import_folder.is_absolute():
            import_folder = config.journal_path.parent / import_folder
        if not import_folder.exists():
            raise FileNotFoundError(f"Import folder does not exist: {import_folder}")
        # Create bank CSV import configuration
        bank_csv_dict: dict = import_conf["bank_csv"]
        bank_csv_dict.update({"account": acc})
        # Loop through CSV files in the import folder
        for file in import_folder.glob("*.csv"):
            bank_csv_dict["file"] = str(file)
            bank_csv = BankCsv(**bank_csv_dict)
            txns = bank_csv.get_new_txns(journal, classifier)
            print(f"Importing {len(txns)} transactions from {file.name} into account '{acc.name}'")
            for t in txns:
                journal.add_txn(t)

def auto_update_journal(journal: Journal, config: Config):
    acc_names = [a.name for a in journal.accounts]
    # Automatically fix statement dates for specified accounts
    for a in config.auto_stmt_date:
        if a not in acc_names:
            raise ValueError(f"Account '{a}' not found in journal")
        fix_statement_date(journal, a)

    # Automatically add balance assertions for specified accounts
    for a, annual_rate in config.auto_balance_assertion.items():
        if a not in acc_names:
            raise ValueError(f"Account '{a}' not found in journal")
        auto_balance_assertion(journal, a, annual_rate)

    # Automatically auto balance for specified accounts
    for a, counter in config.auto_balance.items():
        if a not in acc_names:
            raise ValueError(f"Account '{a}' not found in journal")
        if counter not in acc_names:
            raise ValueError(f"Account '{counter}' not found in journal")
        auto_balance(journal, a, counter)


def fix_statement_date(journal: Journal,
                       account: Account | str):
    """
    Modifies the statement date of postings in the journal to ensure that
    the balance of the specified account matches the balance in the journal.
    """
    account = account.name if isinstance(account, Account) else account
    bs = sorted((b for b in journal.bassertions if b.account.name == account),
                key=lambda b: b.date)
    for b in bs:
        s = journal.account_balance(b.account, b.date, use_stmt_date=True)
        if s != b.balance:
            diff = s - b.balance
            ps2 = journal.find_subset(amnt=diff, account=account,
                                start_date=b.date - timedelta(days=5),
                                end_date=b.date,
                                use_stmt_date=True)
            if ps2:
                print(f"Found {len(ps2)} postings to balance '{account}' on {b.date}.")
                for p in ps2:
                    p.stmt_date = b.date + timedelta(days=1)
            else:
                raise ValueError("Unable to find postings to balance Mastercard BNC.")

def auto_balance_assertion(journal: Journal,
                           account: Account | str,
                           annual_rate: float):
    """
    Automatically adds a balance assertion each month for the specified account
    with the given annual rate.
    """
    account = account.name if isinstance(account, Account) else account
    acc = journal.get_account(account)
    monthly_rate: float = (1.0 + annual_rate) ** (1.0 / 12)
    today = date.today()

    new_bas: list[BAssertion] = []
    b = journal.get_last_balance(account)
    if b is None:
        # We need a starting balance assertion
        raise ValueError(f"No balance assertion for '{account}'.")
    # Ensure that the last balance assertion is at the end of month
    if (b.date + timedelta(days=1)).day != 1:
        raise ValueError(f"Last balance assertion for '{account}' is not at the end of month.")
    nextDate = (b.date + timedelta(days=1)) + relativedelta(months=1) - timedelta(days=1)
    while nextDate < today:
        nextBalance = Decimal((float(b.balance) * monthly_rate)).quantize(Decimal("0.01"))
        b = BAssertion(date=nextDate, account=acc, balance=nextBalance)
        new_bas.append(b)
        nextDate = (nextDate + timedelta(days=1)) + relativedelta(months=1) - timedelta(days=1)
    for x in new_bas:
        print(f"Adding balance assertion for '{account}' on {x.date} with balance {x.balance}")
        journal.add_bassertion(x)

def auto_balance(journal: Journal,
                 account: Account | str,
                 counter_account: Account | str):
    """
    Automatically balances the specified account by adding a new transaction.
    """
    account = account.name if isinstance(account, Account) else account
    bs = sorted((b for b in journal.bassertions if b.account.name == account),
                key=lambda b: b.date)
    for b in bs:
        s = journal.account_balance(b.account, b.date, use_stmt_date=True)
        if s != b.balance:
            diff = b.balance - s
            txn_id = journal.next_txn_id()
            p1 = Posting(txn_id=txn_id, date=b.date, account=b.account, amount=diff)
            if isinstance(counter_account, Account):
                a2 = counter_account
            else:
                a2 = journal.get_account(counter_account)
            p2 = Posting(txn_id=txn_id, date=b.date, account=a2, amount=-diff)
            print(f"Adding auto-balance transaction for '{account}' on {b.date} with amount {diff}.")
            t = Txn(postings=[p1, p2])
            journal.add_txn(t)
