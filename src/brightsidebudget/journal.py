from pathlib import PosixPath
from datetime import date, timedelta
from decimal import Decimal
from typing import Callable, Iterable, Union
from brightsidebudget.account import Account, ChartOfAccounts, QName, load_accounts, write_accounts
from brightsidebudget.bassertion import BAssertion, load_balances, write_bassertions
from brightsidebudget.budget import Budget, RPosting, load_rpostings
from brightsidebudget.txn import Posting, Txn, load_txns, write_txns


class Journal():
    """
    A Journal is a collection of postings that can be used to track the
    financial activities of a person or organization. It also contains a list
    of accounts, balance assertions and budget targets.
    """
    def __init__(self):
        """
        Creates an empty journal.
        """
        self.chartOfAccounts = ChartOfAccounts()
        self.txns_dict: dict[int, Txn] = {}
        self._next_txn_id = 1
        self.budget: Budget = Budget()
        self.bassertions_dict: dict[QName, dict[date, BAssertion]] = {}

    @property
    def next_txn_id(self) -> int:
        return self._next_txn_id

    def txn(self, txnid: int) -> Txn:
        return self.txns_dict[txnid]

    @property
    def txns(self) -> Iterable[Txn]:
        return iter(self.txns_dict.values())

    @property
    def postings(self) -> Iterable[Posting]:
        return (p for t in self.txns_dict.values() for p in t.postings)

    @property
    def bassertions(self) -> Iterable[BAssertion]:
        return (b for bs in self.bassertions_dict.values() for b in bs.values())

    def add_accounts(self, accs: list[Account]):
        """
        Adds a list of accounts to the journal.
        """
        self.chartOfAccounts.add_accounts(accs)

    def add_txns(self, txns: Txn | list[Txn],
                 *, overwrite_txnid: bool = True):
        """
        Adds transactions to the journal.
        The accounts in the postings must exist in the journal.
        The accounts must be leaf accounts.
        """
        if not isinstance(txns, list):
            txns = [txns]

        # Validate postings
        id = self._next_txn_id
        for t in txns:
            for p in t.postings:
                if overwrite_txnid:
                    p.txnid = id
                elif p.txnid in self.txns_dict:
                    raise ValueError(f'Transaction {p.txnid} already exists')

                if not self.chartOfAccounts.is_valid_qname(p.acc_qname):
                    msg = f'Txn {p.txnid}: Account {p.acc_qname} does not exist or is ambiguous'
                    raise ValueError(msg)

                # Update to full qname
                p.acc_qname = self.chartOfAccounts.full_qname(p.acc_qname)

                if not self.chartOfAccounts.is_leaf_account(p.acc_qname):
                    raise ValueError(f'Txn {p.txnid}: Account {p.acc_qname} is not a leaf account')

            id += 1

        for t in txns:
            self.txns_dict[t.txnid] = t

        if overwrite_txnid:
            self._next_txn_id = id
        else:
            max_id = max((t.txnid for t in txns), default=0)
            self._next_txn_id = max(max_id + 1, self._next_txn_id)

    def add_bassertions(self, bassertions: BAssertion | list[BAssertion]):
        """
        Adds a list of balance assertions to the journal.
        The accounts in the balance assertions must exist in the journal.
        The accounts may be leaf accounts or parent accounts.
        """
        if not isinstance(bassertions, list):
            bassertions = [bassertions]

        for b in bassertions:
            if not self.chartOfAccounts.is_valid_qname(b.acc_qname):
                raise ValueError(f'Account {b.acc_qname} does not exist or is ambiguous')

            # Update to full qname
            b.acc_qname = self.chartOfAccounts.full_qname(b.acc_qname)

            # Check for duplicates
            if b.acc_qname not in self.bassertions_dict:
                self.bassertions_dict[b.acc_qname] = {}
            if b.date in self.bassertions_dict[b.acc_qname]:
                raise ValueError(f'BAssertion {b.date} {b.acc_qname} already exists')

            self.bassertions_dict[b.acc_qname][b.date] = b

    def add_targets(self, targets: list[RPosting]):
        """
        Adds a list of budget targets to the journal.
        The accounts in the targets must exist in the journal.
        The accounts must be leaf accounts.
        """
        for t in targets:
            if not self.chartOfAccounts.is_valid_qname(t.acc_qname):
                raise ValueError(f'Account {t.acc_qname} does not exist or is ambiguous')
            if not self.chartOfAccounts.is_leaf_account(t.acc_qname):
                raise ValueError(f'Account {t.acc_qname} is not a leaf account')

            # Update to full qname
            t.acc_qname = self.chartOfAccounts.full_qname(t.acc_qname)

        self.budget.add_targets(targets)

    def balance(self, dt: date, qname: QName | str,
                use_stmt_date: bool = False) -> Decimal:
        """
        Returns the balance of an account at a certain date.

        This function is not optimized for performance.
        """
        if isinstance(qname, str):
            qname = QName(qname=qname)

        def get_date(p: Posting) -> date:
            return p.stmt_date if use_stmt_date else p.date

        balance = Decimal(0)
        full_qname = self.chartOfAccounts.full_qname(qname)
        for p in self.postings:
            if get_date(p) <= dt and (p.acc_qname == full_qname or
                                      p.acc_qname.is_descendant_of(full_qname)):
                balance += p.amount

        return balance

    def flow(self, start_date: date, end_date: date, qname: QName | str,
             use_stmt_date: bool = False) -> Decimal:
        """
        Returns the flow of an account between two dates (inclusive).
        This function is not optimized for performance.
        """
        if start_date > end_date:
            raise ValueError('start_date must be before end_date')
        start_date = start_date - timedelta(days=1)
        return self.balance(end_date, qname, use_stmt_date) - self.balance(start_date, qname,
                                                                           use_stmt_date)

    @classmethod
    def from_csv(cls, *, accounts: str, postings: str | list[str] | None = None,
                 bassertions: str | None = None,
                 targets: str | None = None,
                 encoding: str = 'utf-8'):
        """
        Loads a journal from CSV files.
        """
        if postings is None:
            postings = []
        if isinstance(postings, (str, PosixPath)):
            postings = [postings]

        j = cls()
        accs = load_accounts(accounts, encoding=encoding)
        j.add_accounts(accs)

        txns: list[Txn] = load_txns(postings, encoding=encoding)
        j.add_txns(txns, overwrite_txnid=False)

        if bassertions is not None:
            bs = load_balances(bassertions, encoding=encoding)
            j.add_bassertions(bs)

        if targets is not None:
            ts = load_rpostings(targets, encoding=encoding)
            j.add_targets(ts)

        return j

    def write_accounts(self, file: str, encoding: str = 'utf-8'):
        """
        Writes the accounts to a CSV file.
        """
        write_accounts(accounts=self.chartOfAccounts.accounts, file=file, encoding=encoding)

    def write_bassertions(self, file: str, encoding: str = 'utf-8'):
        """
        Writes the balance assertions to a CSV file.
        """
        bs = [b.copy() for b in self.bassertions]
        for b in bs:
            b.acc_qname = self.chartOfAccounts.short_qname(b.acc_qname)
        write_bassertions(bassertions=bs, file=file, encoding=encoding)

    def write_txns(self, filefunc: str | Callable[[Txn], str], encoding: str = 'utf-8'):
        """
        Writes the transactions to a CSV file.
        """
        txns = [t.copy() for t in self.txns]
        for t in txns:
            for p in t.postings:
                p.acc_qname = self.chartOfAccounts.short_qname(p.acc_qname)
        write_txns(txns=txns, filefunc=filefunc, encoding=encoding)

    def export_txns(self, file: str, encoding: str = 'utf-8',
                    txns: list[Txn] | None = None):
        """
        Exports the transactions to a CSV file with extra fields.
        Perfect for importing into a spreadsheet.
        """
        if txns is None:
            txns = [t.copy() for t in self.txns]
        max_depth = self.chartOfAccounts.max_depth()
        for t in txns:
            all_accs = list(set(self.chartOfAccounts.short_qname(p.acc_qname) for p in t.postings))
            all_accs.sort(key=lambda x: x.sort_key)
            all_accs = [a.qstr for a in all_accs]
            for p in t.postings:
                full_name = p.acc_qname
                p.tags["Nom complet"] = full_name
                p.acc_qname = self.chartOfAccounts.short_qname(p.acc_qname)
                p.tags["Année"] = str(p.date.year)
                p.tags["Mois"] = str(p.date.month)
                p.tags["Txn comptes"] = " | ".join(all_accs)
                for i in range(max_depth):
                    if i < len(full_name):
                        p.tags[f"Compte {i+1}"] = full_name._qlist[i]
                    else:
                        p.tags[f"Compte {i+1}"] = ""
        write_txns(txns=txns, filefunc=file, encoding=encoding)

    def export_budget(self, file: str, start_date: date, end_date: date,
                      counterpart: QName | str, encoding: str = 'utf-8'):
        txns = self.budget.budget_txns(start_date, end_date, counterpart)
        self.export_txns(file, encoding=encoding, txns=txns)

    def failed_bassertions(self) -> list[BAssertion]:
        """
        Returns the list of assertions that do not match the journal balances.
        The stmt_date is used to compute the actual balance.
        """
        ls = []
        bs = sorted(self.bassertions, key=lambda x: x.date)
        acc_balance: dict[QName, Decimal] = {}
        ps_idx = 0
        ps = sorted(self.postings, key=lambda x: x.stmt_date)
        for b in bs:
            # Update the account balances up to the assertion date
            while ps_idx < len(ps):
                p = ps[ps_idx]
                if p.stmt_date > b.date:
                    break
                if p.acc_qname not in acc_balance:
                    acc_balance[p.acc_qname] = Decimal(0)
                acc_balance[p.acc_qname] += p.amount
                ps_idx += 1

            actual = Decimal(0)
            for a, m in acc_balance.items():
                if a == b.acc_qname or a.is_descendant_of(b.acc_qname):
                    actual += m
            if b.balance != actual:
                ls.append(b)
        return ls

    def last_bassertion(self, qname: QName | str) -> Union[BAssertion, None]:
        """
        Returns the last balance assertion for the account.
        """
        bs = self.account_bassertions(qname)
        if bs:
            return bs[-1]
        else:
            return None

    def account_bassertions(self, qname: QName | str) -> list[BAssertion]:
        """
        Returns the list of balance assertions for the account, sorted by date.
        """
        if isinstance(qname, str):
            qname = QName(qname=qname)

        full_qname = self.chartOfAccounts.full_qname(qname)
        bs = self.bassertions_dict.get(full_qname, {}).values()
        return sorted(bs, key=lambda x: x.date)

    def find_subset(self, amnt: Decimal,
                    qname: QName | str,
                    start_date: date,
                    end_date: date,
                    use_stmt_date: bool = False) -> list[Posting] | None:
        """
        Returns a list of postings between start_date and end_date whose sum is
        equal to amnt. The postings closer to the end_date are preferred.

        You can use this function to find the postings that could explain a
        difference between the balance assertion and the actual balance.

        This function is computationally expensive and will almost always find a
        solution if the number of postings is large enough. We recommend using
        a small enough time window to limit the number of postings to consider.
        """
        if isinstance(qname, str):
            qname = QName(qname=qname)

        full_qname = self.chartOfAccounts.full_qname(qname)

        def get_date(p: Posting) -> date:
            return p.stmt_date if use_stmt_date else p.date

        ps = [p for p in self.postings
              if p.acc_qname == full_qname
              and get_date(p) <= end_date
              and get_date(p) >= start_date]

        ps.sort(key=lambda p: get_date(p), reverse=True)
        subset = subset_sum([p.amount for p in ps], amnt)
        if not subset:
            return None
        else:
            return [ps[i] for i in subset]

    def adjust_for_bassertions(self,
                               accounts: list[QName | str],
                               counterparts: list[QName | str],
                               children: list[Union[QName, str, None]] = None,
                               force_zero_txn: bool = False,
                               comment: str | None = None) -> list[Txn]:
        """
        Adjusts the journal to match the balance assertions for the specified
        accounts by creating a new transaction for each balance assertion
        failure.

        The counterpart account is used to balance the transaction. If provided
        child is the account to use instead of the one in the balance assertion.
        It must be a descendant of the account in the balance assertion.

        Use force_zero_txn to create a transaction even if the balance assertion
        is met.

        All lists must have the same length.
        """
        if children is None:
            children = [None] * len(accounts)
        if len(accounts) != len(counterparts) or len(accounts) != len(children):
            raise ValueError('All lists must have the same length')
        txns = []
        for acc, counterpart, child in zip(accounts, counterparts, children):
            acc_qname = self.chartOfAccounts.full_qname(acc)
            counterpart = self.chartOfAccounts.full_qname(counterpart)
            if child is None:
                child = acc_qname
            else:
                child = self.chartOfAccounts.full_qname(child)
                if not (child == acc_qname or child.is_descendant_of(acc_qname)):
                    msg = f'Child account {children} must be a descendant of {acc_qname}'
                    raise ValueError(msg)
            bs = self.account_bassertions(acc_qname)

            for b in bs:
                actual = self.balance(b.date, b.acc_qname, use_stmt_date=True)
                diff = b.balance - actual
                if diff == 0 and not force_zero_txn:
                    continue

                txnid = self.next_txn_id
                p1 = Posting(txnid=txnid, date=b.date, acc_qname=child, amount=diff,
                             comment=comment)
                p2 = Posting(txnid=txnid, date=b.date, acc_qname=counterpart, amount=-diff,
                             comment=comment)
                t = Txn([p1, p2])
                self.add_txns(t, overwrite_txnid=False)
                txns.append(t)
        return txns


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
