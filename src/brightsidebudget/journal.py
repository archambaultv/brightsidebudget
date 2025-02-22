
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Callable, Union
from brightsidebudget.account import Account
from brightsidebudget.bassertion import BAssertion
from brightsidebudget.posting import Posting
from brightsidebudget.utils import exit_on_error, print_yellow


class Journal:
    def __init__(self, *, accounts: list[Account], postings: list[Posting],
                 bassertions: list[BAssertion]):
        self.accounts = accounts
        self.accounts_dict = {a.name: a for a in accounts}
        self.bassertions = bassertions
        self.postings = postings

    def get_account(self, account: str) -> Account:
        return self.accounts_dict[account]

    def check_journal(self, *,
                      check_bassertion: bool = True,
                      check_1_n: bool = True):
        self.check_accounts()
        self.check_bassertions()
        self.check_postings(check_bassertion=check_bassertion, check_1_n=check_1_n)

    def check_accounts(self):
        accs = set()
        acc_numbers = set()
        for a in self.accounts:
            if a.name in accs:
                exit_on_error(f"Duplicate account '{a.name}'")
            accs.add(a.name)
            if a.number in acc_numbers:
                exit_on_error(f"Duplicate account number '{a.number}'")
            acc_numbers.add(a.number)

    def check_postings(self, *,
                       check_bassertion: bool = True,
                       check_1_n: bool = True):
        # Check that all accounts are in the accounts file
        for p in self.postings:
            if p.account.name not in self.accounts_dict:
                exit_on_error(f"Account '{p.account.name}' not in accounts file")

        # Group by txnid
        tnx_dict = Posting.get_txns_dict(self.postings)

        # Check txn same date and balance
        for txnid, ps2 in tnx_dict.items():
            if len(set(p.date for p in ps2)) != 1:
                exit_on_error(f"Txn {txnid} has different dates")
            pNone = None
            for p in ps2:
                if p.amount is None:
                    if pNone is not None:
                        exit_on_error(f"Txn {txnid} has more than one None amount")
                    pNone = p
            s = sum(p.amount for p in ps2 if p.amount is not None)
            if pNone is not None:
                print_yellow(f"Txn {txnid} has None amount.")
                pNone.amount = -s
                s = 0

            if s != 0:
                exit_on_error(f"Txn {txnid} does not balance. Total: {s}")

        # Check balance assertions
        if check_bassertion:
            for b in self.bassertions:
                s = self.balance(b.account, b.date)
                if s != b.balance:
                    exit_on_error(f"Assertion {b.date} for '{b.account}' does not balance. "
                                  f"Expected: {b.balance}, actual: {s}. "
                                  f"Diff: {b.balance - s}")

        # Display a warning in yellow if "Dépenses non classées" is used
        for p in self.postings:
            if p.account.name == "Dépenses non classées":
                print_yellow(f"Dépenses non classées (txn {p.txn_id})")

        # Display a warning in yellow if a posting in null
        for p in self.postings:
            if p.amount == 0:
                print_yellow(f"Posting {p.txn_id} is null")

        # Display a warning in yellow if transaction is not 1:n
        if check_1_n:
            for txnid, ps2 in tnx_dict.items():
                pos = len([p for p in ps2 if p.amount > 0])
                neg = len([p for p in ps2 if p.amount < 0])
                if pos == 1 or neg == 1:
                    continue
                print_yellow(f"Transaction {txnid} is not 1:n")

    def balance(self, account: str | Account, date: date) -> Decimal:
        if isinstance(account, Account):
            account = account.name
        s = sum(p.amount for p in self.postings
                if p.account.name == account and p.stmt_date <= date)
        return s

    def flow(self, account: str | Account,
             start_date: date, end_date: date) -> Decimal:
        if isinstance(account, Account):
            account = account.name
        s = sum(p.amount for p in self.postings
                if p.account.name == account
                and p.date <= end_date
                and p.date >= start_date)
        return s

    def next_txn_id(self) -> int:
        return max((p.txn_id for p in self.postings), default=0) + 1

    def known_keys(self) -> dict[tuple[date, str, Decimal, str], int]:
        known = defaultdict(int)
        for p in self.postings:
            known[p.dedup_key()] += 1
        return known

    def get_last_balance(self, account: str | Account) -> Union['BAssertion', None]:
        if isinstance(account, Account):
            account = account.name
        last = None
        for b in self.bassertions:
            if b.account.name == account:
                if last is None or b.date > last.date:
                    last = b
        return last

    def check_bassertions(self):
        # Check that all accounts are in the accounts file
        for b in self.bassertions:
            if b.account.name not in self.accounts_dict:
                exit_on_error(f"Account '{b.account}' not in accounts file (balance assertion)")

        # Check that all balance assertions are unique
        s = set()
        for b in self.bassertions:
            k = b.dedup_key()
            if k in s:
                exit_on_error(f"Duplicate balance assertion {k}")
            s.add(k)

    def write_journal(self, *,
                      account_filename: str = "Comptes.csv",
                      posting_filename: str | Callable[[Posting], str] = "Transactions.csv",
                      bassertion_filename: str = "Soldes.csv",
                      renumber: bool = False,
                      check_bassertion: bool = True,
                      check_1_n: bool = True):
        self.check_journal(check_bassertion=check_bassertion, check_1_n=check_1_n)
        Account.write_accounts(self.accounts, filename=account_filename)
        Posting.write_postings(ps=self.postings, renumber=renumber, filename=posting_filename)
        BAssertion.write_assertions(self.bassertions, filename=bassertion_filename)

    @classmethod
    def get_journal(cls, *,
                    account_filename: str = "Comptes.csv",
                    posting_filename: str | list[str] = "Transactions.csv",
                    bassertion_filename: str = "Soldes.csv",
                    check_bassertion: bool = True,
                    check_1_n: bool = True):
        if isinstance(posting_filename, str):
            posting_filename = [posting_filename]
        j = cls(accounts=Account.get_accounts(filename=account_filename),
                postings=Posting.get_postings(filenames=posting_filename),
                bassertions=BAssertion.get_assertions(filename=bassertion_filename))
        j.check_journal(check_bassertion=check_bassertion, check_1_n=check_1_n)
        return j
