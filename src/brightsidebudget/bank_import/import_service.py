from datetime import date, timedelta
from decimal import Decimal
import logging
from pathlib import Path

from dateutil.relativedelta import relativedelta

from brightsidebudget.account.account import Account
from brightsidebudget.bank_import.bank_csv import BankCsv
from brightsidebudget.bank_import.classifier import IClassifier, RuleClassifier
from brightsidebudget.bassertion.bassertion import BAssertion
from brightsidebudget.config import Config
from brightsidebudget.journal.journal import Journal
from brightsidebudget.txn.posting import Posting
from brightsidebudget.txn.txn import Txn


class ImportService:
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def load_and_update_journal(self) -> Journal:
        """
        Loads the journal from the configured path and updates it based on the configuration.
        Does not save the journal to disk.
        """
        journal = self.config.get_journal(skip_check=True)
        self.auto_update_journal(journal, self.config)
        txns = self.import_new_txns(journal, self.config)
        self.new_txns_report(txns)
        return journal

    def new_txns_report(self, txns: list[Txn]):
        """
        Prints a report of the new transactions imported.
        """
        # Number of uncategorized transactions
        uncategorized = [t for t in txns if t.is_uncategorized()]
        descriptions = {}
        for t in uncategorized:
            descriptions[t.postings[0].stmt_desc] = descriptions.get(t.postings[0].stmt_desc, 0) + 1
        if uncategorized:
            print(f"Found {len(uncategorized)} uncategorized transactions with {len(descriptions)} unique descriptions:")
            xs = sorted(descriptions.items(), key=lambda x: x[1], reverse=True)
            xs = xs[:10]  # Show top 10 descriptions
            max_desc_width = max(len(desc) for desc, _ in xs) if xs else 0
            max_count_width = len(str(max(count for _, count in xs))) if xs else 0
            for desc, count in xs:
                print(f"  - {desc:<{max_desc_width}} ({count:>{max_count_width}} occurrences)")

    def import_new_txns(self, journal: Journal, config: Config) -> list[Txn]:
        """
        Imports new transactions into the journal based on the configuration.
        Modifies the journal in place and returns the new transactions added.
        """
        if not config.importation:
            return []

        new_txns: list[Txn] = []
        for import_conf in config.importation:
            # Create classifier
            acc = journal.get_account(import_conf["account"])
            acc_dict = {a.name: a for a in journal.accounts}
            classifier = RuleClassifier(
                file=import_conf["rules"]["file"],
                accounts=acc_dict,
                logger=self.logger
            )
            msg = f"Using classifier from '{import_conf['rules']['file']}' for account '{acc.name}'"
            self.logger.info(msg)

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
                self.logger.info(f"Processing file: '{file.name}' for account '{acc.name}'")
                bank_csv_dict["file"] = str(file)
                bank_csv = BankCsv(**bank_csv_dict)
                bank_ps = bank_csv.get_bank_postings()
                txns = self.get_new_txns(journal, bank_ps, classifier)
                msg = f"Importing {len(txns)} transactions from '{file.name}' into account '{acc.name}'"
                self.logger.info(msg)
                print(msg)
                new_txns.extend(txns)
                for t in txns:
                    journal.add_txn(t)
        return new_txns

    def auto_update_journal(self, journal: Journal, config: Config):
        acc_names = [a.name for a in journal.accounts]
        # Automatically fix statement dates for specified accounts
        for a in config.auto_stmt_date:
            if a not in acc_names:
                raise ValueError(f"Account '{a}' not found in journal")
            self.fix_statement_date(journal, a)

        # Automatically add balance assertions for specified accounts
        for a, annual_rate in config.auto_balance_assertion.items():
            if a not in acc_names:
                raise ValueError(f"Account '{a}' not found in journal")
            self.auto_balance_assertion(journal, a, annual_rate)

        # Automatically auto balance for specified accounts
        for a, counter in config.auto_balance.items():
            if a not in acc_names:
                raise ValueError(f"Account '{a}' not found in journal")
            if counter not in acc_names:
                raise ValueError(f"Account '{counter}' not found in journal")
            self.auto_balance(journal, a, counter)


    def fix_statement_date(self, journal: Journal,
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
                    msg = f"Found {len(ps2)} postings to balance '{account}' statement date on {b.date}."
                    self.logger.info(msg)
                    print(msg)
                    for p in ps2:
                        p.stmt_date = b.date + timedelta(days=1)
                else:
                    raise ValueError("Unable to find postings to balance Mastercard BNC.")

    def auto_balance_assertion(self, journal: Journal,
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
            msg = f"Adding balance assertion for '{account}' on {x.date} with balance {x.balance}"
            self.logger.info(msg)
            print(msg)
            journal.add_bassertion(x)

    def auto_balance(self, journal: Journal,
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
                msg = f"Adding auto-balance transaction for '{account}' on {b.date} with amount {diff}."
                self.logger.info(msg)
                print(msg)
                t = Txn(postings=[p1, p2])
                journal.add_txn(t)


    def get_new_txns(self, journal: Journal,
                     bank_ps: list[Posting],
                     classifier: IClassifier) -> list[Txn]:
        """
        Classifies the bank postings and returns new transactions that are not already in the journal.
        It is expected that all postings in `bank_ps` belong to the same account.
        """
        if not bank_ps:
            return []

        # Remove postings that are already in the database
        acc = bank_ps[0].account
        self.logger.info(f"Classifying {len(bank_ps)} bank postings for account '{acc.name}'...")
        last = journal.get_last_balance(acc)
        known = journal.known_keys()
        new_ps = []
        for p in bank_ps:
            if last is not None and p.date <= last.date:
                continue
            if p.dedup_key() in known:
                known[p.dedup_key()] -= 1
                if known[p.dedup_key()] == 0:
                    del known[p.dedup_key()]
                continue
            self.logger.debug(f"New posting: {p}")
            new_ps.append(p)
        nb_old = len(bank_ps) - len(new_ps)
        self.logger.info(f"Found {len(new_ps)} new postings after removing {nb_old} old postings.")

        # Classify the new postings
        new_txns: list[Txn] = []
        for p in new_ps:
            txns = classifier.classify(posting=p)
            if not txns:
                continue
            if isinstance(txns, Txn):
                txns = [txns]
            new_txns.extend(txns)

        # Renumber the transactions
        next_txnid = journal.next_txn_id()
        for i, txn in enumerate(new_txns, start=next_txnid):
            ps = []
            for p in txn.postings:
                # Create a new posting with the same data but a new txn_id
                ps.append(p.model_copy(update={"txn_id": i}))
            new_txns[i - next_txnid] = Txn(postings=ps)

        return new_txns
