
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
import os
import shutil
from typing import Callable, Union
from brightsidebudget.account import Account
from brightsidebudget.bassertion import BAssertion
from brightsidebudget.posting import Posting
from brightsidebudget.bsberror import BSBError
from brightsidebudget.txn import Txn


class Journal:
    def __init__(self, first_fiscal_month: int = 1):
        self.first_fiscal_month = first_fiscal_month
        self._accounts: list[Account] = []
        self._accounts_dict: dict[str, Account] = {}
        self._bassertions: list[BAssertion] = []
        self._txn_dict: list[int, Txn] = {}
        self._postings: list[Posting] = []

    @property
    def accounts(self) -> list[Account]:
        return self._accounts

    @property
    def accounts_dict(self) -> dict[str, Account]:
        return self._accounts_dict

    @property
    def bassertions(self) -> list[BAssertion]:
        return self._bassertions

    @property
    def txn_dict(self) -> dict[int, Txn]:
        return self._txn_dict

    @property
    def postings(self) -> list[Posting]:
        return self._postings

    def fiscal_year(self, d: date) -> int:
        """
        Returns the fiscal year for a given date.
        The fiscal year starts on the first_fiscal_month.

        Example:
        - first_fiscal_month = 7
        - d = 2022-06-30 -> fiscal year = 2022
        - d = 2022-07-01 -> fiscal year = 2023
        """
        if self.first_fiscal_month == 1:
            return d.year
        if d.month >= self.first_fiscal_month:
            return d.year + 1
        return d.year

    def txns(self) -> list[Txn]:
        return list(self.txn_dict.values())

    def get_account(self, account: str) -> Account:
        return self.accounts_dict[account]

    def add_account(self, account: Account):
        if account.name in self.accounts_dict:
            raise BSBError(f"Account '{account.name}' already exists")
        s_number = set(a.number for a in self.accounts)
        if account.number in s_number:
            raise BSBError(f"Account number '{account.number}' already exists")
        self.accounts.append(account)
        self.accounts_dict[account.name] = account

    def add_bassertion(self, b: BAssertion):
        # Check that account is in the accounts file
        if b.account.name not in self.accounts_dict:
            raise BSBError(f"Account '{b.account}' not in accounts file (balance assertion)")

        # Check that all balance assertions are unique
        s = {b.dedup_key() for b in self.bassertions}
        if b.dedup_key() in s:
            raise BSBError(f"Duplicate balance assertion {b.dedup_key()}")
        self.bassertions.append(b)

    def add_txn(self, t: Txn):
        for p in t:
            if p.account.name not in self.accounts_dict:
                raise BSBError(f"Account '{p.account}' not in accounts file (txn {t.txn_id})")
        if t.txn_id in self.txn_dict:
            raise BSBError(f"Transaction '{t.txn_id}' already exists")
        self.txn_dict[t.txn_id] = t
        self.postings.extend(t)

    def not_1_n_txns(self) -> list[Txn]:
        return [t for t in self.txn_dict.values() if not t.is_1_n()]

    def zero_amount_txns(self) -> list[Txn]:
        return [t for t in self.txn_dict.values() if t.has_zero_amount()]

    def uncategorized_txns(self) -> list[Txn]:
        return [t for t in self.txn_dict.values() if t.is_uncategorized()]

    def balance(self, account: str | Account, date: date,
                use_stmt_date: bool = False) -> Decimal:
        if isinstance(account, Account):
            account = account.name

        def get_date(p: Posting):
            return p.stmt_date if use_stmt_date else p.date

        s = sum(p.amount for p in self.postings
                if p.account.name == account and get_date(p) <= date)
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

    def failed_bassertions(self) -> list[BAssertion]:
        errors = []
        for b in self.bassertions:
            s = self.balance(b.account, b.date, use_stmt_date=True)
            if s != b.balance:
                errors.append(b)
        return errors

    def write_journal(self, *,
                      account_filename: str = "Comptes.csv",
                      posting_filename: str | Callable[[Posting], str] = "Transactions.csv",
                      bassertion_filename: str = "Soldes.csv",
                      backup_dir: str | None = None,
                      renumber: bool = False):
        if backup_dir:
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            if not os.path.isdir(backup_dir):
                raise BSBError(f"{backup_dir} is not a directory")
            if isinstance(posting_filename, str):
                posting_files = [posting_filename]
            else:
                posting_files = list({posting_filename(p) for p in self.postings})
            fs = [account_filename, bassertion_filename] + posting_files
            timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
            for f in fs:
                basename = os.path.basename(f)
                backup_f = os.path.join(backup_dir, f"{timestamp}_{basename}")
                if os.path.exists(f):
                    shutil.copy(f, backup_f)
        Account.write_accounts(self.accounts, filename=account_filename)
        Posting.write_postings(ps=self.postings, renumber=renumber, filename=posting_filename)
        BAssertion.write_assertions(self.bassertions, filename=bassertion_filename)

    @classmethod
    def get_journal(cls, *,
                    account_filename: str = "Comptes.csv",
                    posting_filename: str | list[str] = "Transactions.csv",
                    bassertion_filename: str = "Soldes.csv"):
        if isinstance(posting_filename, str):
            posting_filename = [posting_filename]

        j = cls()
        accs = Account.get_accounts(filename=account_filename)
        for a in accs:
            j.add_account(a)

        ps = Posting.get_postings(filenames=posting_filename, accounts=j.accounts_dict)
        for t in Txn.from_postings(ps):
            j.add_txn(t)

        bs = BAssertion.get_assertions(filename=bassertion_filename, accounts=j.accounts_dict)
        for b in bs:
            j.add_bassertion(b)
        return j

    def find_subset(self, *,
                    amnt: Decimal,
                    account: str | Account,
                    start_date: date,
                    end_date: date,
                    use_stmt_date: bool = False) -> list['Posting'] | None:
        if isinstance(account, Account):
            account = account.name

        def get_date(p: Posting) -> date:
            return p.stmt_date if use_stmt_date else p.date

        ps = [p for p in self.postings
              if p.account.name == account
              and get_date(p) <= end_date
              and get_date(p) >= start_date]

        ps.sort(key=lambda p: get_date(p), reverse=True)
        subset = subset_sum([p.amount for p in ps], amnt)
        if not subset:
            return None
        else:
            return [ps[i] for i in subset]


def subset_sum(amounts: list[Decimal], target: Decimal) -> list[int]:
    """
    Finds a subset of the amounts that sum to the target amount.
    Amounts at the front of the list are preferred.

    Returns the positions of the subset in the original list
    or an empty list if no subset is found.
    """
    sum_dict: dict[Decimal, list[int]] = {}
    for i, p in enumerate(amounts):
        diff = target - p
        # Is p the target?
        if diff == Decimal(0):
            return [i]

        # Is there a diff in the dict that is the target?
        if diff in sum_dict:
            ls = sum_dict[diff]
            ls.append(i)
            return ls

        # Too bad, we have to add p to the dict
        for k, v in list(sum_dict.items()):  # Make a copy of the items because we mutate the dict
            new_sum = k + p
            if new_sum not in sum_dict:
                ls = v.copy()
                ls.append(i)
                sum_dict[new_sum] = ls
        if p not in sum_dict:
            sum_dict[p] = [i]
    return []
