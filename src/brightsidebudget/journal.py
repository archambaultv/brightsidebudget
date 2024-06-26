
from collections import defaultdict
from collections.abc import MutableMapping
import csv
import networkx as nx
from datetime import date, timedelta
from decimal import Decimal
from typing import Union

from pydantic import BaseModel, Field


class Account(MutableMapping):
    """
    A dictionary-like object that represents an account.
    The key 'Name' and 'Parent' are always present.
    Provides 'name' and 'parent' attributes for convenience.
    """
    def __init__(self, name: str, parent: str = None, tags: dict = None):
        self._data = tags.copy() if tags is not None else {}
        self._data["Name"] = name
        self._data["Parent"] = parent
        self._check_all()

    @property
    def name(self):
        return self._data["Name"]

    @name.setter
    def name(self, value):
        self._data["Name"] = value
        self._check_name()

    @property
    def parent(self):
        return self._data["Parent"]

    @parent.setter
    def parent(self, value):
        self._data["Parent"] = value
        self._check_parent()

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value
        if key == "Name":
            self._check_name()
        if key == "Parent":
            self._check_parent()

    def __delitem__(self, key):
        if key in ["Name", "Parent"]:
            raise ValueError("Cannot delete {key} key")
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __str__(self):
        return f"Account({self.name})"

    def update(self, *args, **kwargs):
        self._data.update(*args, **kwargs)
        self._check_all()

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def copy(self):
        """
        Return a shallow copy of the account.
        """
        a = Account.__new__(Account)
        a._data = self._data.copy()
        return a

    def get_dict(self) -> dict:
        """
        Return the underlying dictionary.
        Any changes to the dictionary will affect the account.
        """
        return self._data

    def _check_all(self):
        self._check_name()
        self._check_parent()

    def _check_parent(self):
        if not isinstance(self._data["Parent"], (str, type(None))):
            raise ValueError("Parent must be a string or None")
        if self._data["Parent"] == "":
            self._data["Parent"] = None

    def _check_name(self):
        if not isinstance(self._data["Name"], str):
            raise ValueError("Name must be a string")
        if self._data["Name"] == "":
            raise ValueError("Name cannot be an empty string")

    @classmethod
    def from_dict(cls, d: dict, copy: bool = False) -> 'Account':
        """
        Create an account from a dictionary.
        The 'Name' key is required.
        If copy is True, a shallow copy of the dictionary is made.
        """
        if "Name" not in d:
            raise ValueError("Missing Name key in account dict")
        a = cls.__new__(cls)
        a._data = d.copy() if copy else d
        if "Parent" not in a._data:
            a._data["Parent"] = None
        a._check_all()
        return a


class Posting(MutableMapping):
    """
    A dictionary-like object that represents a posting.
    The key 'Txn', 'Date', 'Account' and 'Amount' are always present.
    Provides 'txn', 'date', 'account' and 'amount' attributes for convenience.
    """
    def __init__(self, txn: int, date: date, account: str, amount: Decimal,
                 tags: dict = None):
        self._data = tags.copy() if tags is not None else {}
        self._data["Txn"] = txn
        self._data["Date"] = date
        self._data["Account"] = account
        self._data["Amount"] = amount
        self._check_all()

    @property
    def txn(self) -> int:
        return self._data["Txn"]

    @txn.setter
    def txn(self, value: int):
        self._data["Txn"] = value
        self._check_txn()

    @property
    def date(self) -> date:
        return self._data["Date"]

    @date.setter
    def date(self, value: date):
        self._data["Date"] = value
        self._check_date()

    @property
    def account(self) -> str:
        return self._data["Account"]

    @account.setter
    def account(self, value: str):
        self._data["Account"] = value
        self._check_account()

    @property
    def amount(self) -> Decimal:
        return self._data["Amount"]

    @amount.setter
    def amount(self, value: Decimal):
        self._data["Amount"] = value
        self._check_amount()

    def __str__(self):
        return f"Posting({self.txn}, {self.date}, {self.account}, {self.amount})"

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value
        if key == "Txn":
            self._check_txn()
        if key == "Date":
            self._check_date()
        if key == "Account":
            self._check_account()
        if key == "Amount":
            self._check_amount()

    def __delitem__(self, key):
        if key in ["Txn", "Date", "Account", "Amount"]:
            raise ValueError(f"Cannot delete '{key}' key")
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def update(self, *args, **kwargs):
        self._data.update(*args, **kwargs)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def copy(self):
        """
        Return a shallow copy of the posting.
        """
        p = Posting.__new__(Posting)
        p._data = self._data.copy()
        return p

    def fingerprint(self, tags: list[str] = None) -> tuple:
        """
        Return a tuple that represents the posting.
        The tuple is used to compare postings and find duplicates.
        """
        if tags is None:
            tags = []
        return tuple([self.date, self.account, self.amount] +
                     [self._data[k] for k in tags])

    @classmethod
    def from_dict(cls, d: dict, copy: bool = False) -> 'Posting':
        """
        Create a posting from a dictionary.
        The 'Txn', 'Date', 'Account' and 'Amount' keys are required.
        If copy is True, a shallow copy of the dictionary is made.
        """
        for k in ["Txn", "Date", "Account", "Amount"]:
            if k not in d:
                raise ValueError(f"Missing '{k}' key in posting dict")
        p = cls.__new__(cls)
        p._data = d.copy() if copy else d
        p._check_all()
        return p

    def get_dict(self) -> dict:
        """
        Return the underlying dictionary.
        Any changes to the dictionary will affect the posting.
        """
        return self._data

    def _check_all(self):
        self._check_account()
        self._check_txn()
        self._check_amount()
        self._check_date()

    def _check_account(self):
        if not isinstance(self._data["Account"], str):
            raise ValueError("Account must be a string")
        if self._data["Account"] == "":
            raise ValueError("Account cannot be an empty string")

    def _check_date(self):
        if not isinstance(self._data["Date"], date):
            self._data["Date"] = date.fromisoformat(self._data["Date"])

    def _check_amount(self):
        if not isinstance(self._data["Amount"], Decimal):
            self._data["Amount"] = Decimal(str(self._data["Amount"]))

    def _check_txn(self):
        if not isinstance(self._data["Txn"], int):
            self._data["Txn"] = int(self._data["Txn"])


class BAssertion(MutableMapping):
    """
    A dictionary-like object that represents a balance assertion.
    The key 'Date', 'Account', 'Balance' and 'Include children"' are always present.
    Provides 'date', 'account', 'balance' and 'include_children' attributes for convenience.
    """
    def __init__(self, date: date, account: str, balance: Decimal, include_children: bool = True,
                 tags: dict = None):
        self._data = tags.copy() if tags is not None else {}
        self._data["Date"] = date
        self._data["Account"] = account
        self._data["Balance"] = balance
        self._data["Include children"] = include_children
        self._check_all()

    @property
    def date(self) -> date:
        return self._data["Date"]

    @date.setter
    def date(self, value: date):
        self._data["Date"] = value
        self._check_date()

    @property
    def account(self) -> str:
        return self._data["Account"]

    @account.setter
    def account(self, value: str):
        self._data["Account"] = value
        self._check_account()

    @property
    def balance(self) -> Decimal:
        return self._data["Balance"]

    @balance.setter
    def balance(self, value: Decimal):
        self._data["Balance"] = value
        self._check_balance()

    @property
    def include_children(self) -> bool:
        return self._data["Include children"]

    @include_children.setter
    def include_children(self, value: bool):
        self._data["Include children"] = value
        self._check_include_children()

    def __str__(self):
        return f"BAssertion({self.date}, {self.account}, {self.balance}, \
                 {self.include_children})"

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value
        if key == "Date":
            self._check_date()
        if key == "Account":
            self._check_account()
        if key == "Balance":
            self._check_balance()
        if key == "Include children":
            self._check_include_children()

    def __delitem__(self, key):
        if key in ["Date", "Account", "Balance", "Include children"]:
            raise ValueError(f"Cannot delete '{key}' key")
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def update(self, *args, **kwargs):
        self._data.update(*args, **kwargs)
        self._check_all()

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def copy(self):
        """
        Return a shallow copy of the balance assertion.
        """
        b = BAssertion.__new__(BAssertion)
        b._data = self._data.copy()
        return b

    @classmethod
    def from_dict(cls, d: dict, copy: bool = False) -> 'BAssertion':
        """
        Create a balance assertion from a dictionary.
        The 'Date', 'Account' and 'Balance' keys are required.
        If copy is True, a shallow copy of the dictionary is made.
        """
        for k in ["Date", "Account", "Balance"]:
            if k not in d:
                raise ValueError(f"Missing '{k}' key in balance assertion dict")
        ba = cls.__new__(cls)
        ba._data = d.copy() if copy else d
        if "Include children" not in d:
            ba._data["Include children"] = True
        ba._check_all()
        return ba

    def _check_all(self):
        self._check_account()
        self._check_balance()
        self._check_date()
        self._check_include_children()

    def _check_account(self):
        if not isinstance(self._data["Account"], str):
            raise ValueError("Account must be a string")
        if self._data["Account"] == "":
            raise ValueError("Account cannot be an empty string")

    def _check_include_children(self):
        if not isinstance(self._data["Include children"], bool):
            if self._data["Include children"] in ["True", "False"]:
                self._data["Include children"] = self._data["Include children"] == "True"

    def _check_date(self):
        if not isinstance(self._data["Date"], date):
            self._data["Date"] = date.fromisoformat(self._data["Date"])

    def _check_balance(self):
        if not isinstance(self._data["Balance"], Decimal):
            self._data["Balance"] = Decimal(str(self._data["Balance"]))

    def get_dict(self) -> dict:
        """
        Return the underlying dictionary.
        Any changes to the dictionary will affect the balance assertion.
        """
        return self._data


class BAssertionFail():
    def __init__(self, bassertion: BAssertion, actual_balance: Decimal):
        self.bassertion = bassertion
        self.actual_balance = actual_balance

    def diff(self) -> Decimal:
        """
        The difference between the expected balance and the actual balance.
        """
        return self.bassertion.balance - self.actual_balance

    def __str__(self):
        return f"BAssertionFail({self.bassertion}, {self.actual_balance})"

    def error_msg(self):
        s = f"Balance of {self.bassertion.account} on {self.bassertion.date} is "
        s += f"{self.actual_balance} instead of {self.bassertion.balance}. Diff: {self.diff()}"
        return s


class AccountExtraTags(BaseModel):
    depth: bool = Field(default=True)
    depth_tag: str = Field(min_length=1, default="Account depth")
    depth_start: int = Field(ge=0, default=1)
    hierarchy: bool = Field(default=True)
    hierarchy_tag_format: str = Field(min_length=1, default="Hierarchy depth {}")

    @staticmethod
    def no_extras() -> 'AccountExtraTags':
        return AccountExtraTags(depth=False, hierarchy=False)


class PostingExtraTags(BaseModel):
    account_tags: bool = Field(default=True)
    account_tags_extra: AccountExtraTags = Field(default_factory=AccountExtraTags)
    future_date: bool = Field(default=True)
    future_date_tag: str = Field(min_length=1, default="Future date")
    last_x_days: list[int] = Field(default_factory=lambda: [30, 91, 182, 365])
    last_x_days_tag_format: str = Field(min_length=1, default="Last {} days")
    year: bool = Field(default=True)
    year_tag: str = Field(min_length=1, default="Year")
    month: bool = Field(default=True)
    month_tag: str = Field(min_length=1, default="Month")
    txn_accounts: bool = Field(default=True)
    txn_accounts_tag: str = Field(min_length=1, default="Txn accounts")
    txn_accounts_as_str: bool = Field(default=False)
    txn_accounts_join: str = Field(min_length=1, default=" | ")
    first_fiscal_month: int = Field(ge=1, le=12, default=1)
    fiscal_year: bool = Field(default=True)
    fiscal_year_tag: str = Field(min_length=1, default="Fiscal year")
    fiscal_month: bool = Field(default=True)
    fiscal_month_tag: str = Field(min_length=1, default="Fiscal month")

    @staticmethod
    def no_extras() -> 'PostingExtraTags':
        return PostingExtraTags(account_tags=False,
                                future_date=False, last_x_days=[],
                                year=False, month=False, txn_accounts=False,
                                fiscal_year=False, fiscal_month=False)


class Journal():
    def __init__(self, accounts: list[Account], postings: list[Posting],
                 bassertions: list[BAssertion] = None):
        self.accounts = accounts
        self.postings = postings
        self.bassertions = bassertions if bassertions is not None else []
        self.accounts_graph: nx.DiGraph = None  # Also serves as a dict of accounts
        self.roots: list[Account] = None
        self.postings_by_txn: dict[int, list[Posting]] = None
        self.postings_by_acc: dict[str, list[Posting]] = None
        # Dictionary of account daily flow and balance. For each account we
        # store the minimum date, the maximum index where the balance is valid
        # and a list of tuples with the daily flow and balance. The balance can
        # become invalid when a posting is added to the account. It will be
        # recomputed when needed.
        self.balances: dict[str, tuple[date, int, list[tuple[Decimal, Decimal]]]] = None
        self.bassertions_by_acc: dict[str, list[BAssertion]] = None

        self._init()

    def _init(self):
        # Verify accounts
        seen = set()
        for a in self.accounts:
            if a.name in seen:
                raise ValueError(f"Duplicate account {a.name}")
            seen.add(a.name)
        self.accounts_graph = nx.DiGraph()
        for acc in self.accounts:
            self.accounts_graph.add_node(acc.name, account=acc)
        for acc in self.accounts:
            p = acc.parent
            if p:
                if p not in self.accounts_graph:
                    raise ValueError(f"Unknown parent: {p}")
                self.accounts_graph.add_edge(p, acc.name)
        if not nx.is_directed_acyclic_graph(self.accounts_graph):
            cycle = nx.find_cycle(self.accounts_graph)
            msg = " -> ".join([x for x, _ in cycle])
            msg = f"{msg} -> {cycle[0][0]}"
            raise ValueError(f"Cycle in accounts: {msg}")
        for p in self.postings:
            if p.account not in self.accounts_graph:
                raise ValueError(f"Unknown account: {p.account}")
        for ba in self.bassertions:
            if ba.account not in self.accounts_graph:
                raise ValueError(f"Unknown account: {ba.account}")

        # Add useful information to accounts graph
        self.roots = [self.accounts_graph.nodes[n]["account"]
                      for (n, degree) in self.accounts_graph.in_degree
                      if degree == 0]
        for r in self.roots:
            self.accounts_graph.nodes[r.name]["root"] = r
            for n in nx.descendants(self.accounts_graph, r.name):
                self.accounts_graph.nodes[n]["root"] = r
        for n in self.accounts_graph.nodes:
            self.accounts_graph.nodes[n]["depth"] = len(nx.ancestors(self.accounts_graph, n))

        # Compute txns_by_id and txns_by_acc
        self.postings_by_txn = {}
        self.postings_by_acc = {acc.name: [] for acc in self.accounts}
        for p in self.postings:
            if p.txn not in self.postings_by_txn:
                self.postings_by_txn[p.txn] = []
            self.postings_by_txn[p.txn].append(p)
            self.postings_by_acc[p.account].append(p)

        # Verify txns
        for k, v in self.postings_by_txn.items():
            s = sum([t.amount for t in v])
            if s != Decimal("0"):
                raise ValueError(f"Txn {k} is not balanced. Sum: {s}")
            dt_count = len({t.date for t in v})
            if dt_count != 1:
                raise ValueError(f"Txn {k} has {dt_count} dates")

        # Verify bassertions
        seen = set()
        for ba in self.bassertions:
            if (ba.date, ba.account) in seen:
                raise ValueError(f"Duplicate bassertion: {ba.date} {ba.account}")
            seen.add((ba.date, ba.account))

        # Initialize balances
        self.balances = {}
        for acc in self.accounts:
            self.balances[acc.name] = (None, None, None)

        # Compute bassertions_by_acc
        self.bassertions_by_acc = {acc.name: [] for acc in self.accounts}
        for ba in self.bassertions:
            self.bassertions_by_acc[ba.account].append(ba)

    def _init_balance(self, account: str) -> tuple[date, int, list[tuple[Decimal, Decimal]]]:
        ps = self.postings_by_acc[account]
        if not ps:
            return (None, None, [])
        min_date = min(t.date for t in ps)
        min_date = date(min_date.year, 1, 1)
        max_date = max(t.date for t in ps)
        max_date = date(max_date.year, 12, 31)

        # To make our lives easier, we add all dates. Since there is only 365
        # days in a year and no one keeps 10 000 years of financial records,
        # this is not a big deal.

        xs = [Decimal("0") for _ in range((max_date - min_date).days + 1)]

        # Compute flow
        for p in ps:
            idx = (p.date - min_date).days
            xs[idx] += p.amount

        # Compute balance
        total = Decimal("0")
        for idx, v in enumerate(xs):
            total += v
            xs[idx] = (v, total)

        self.balances[account] = (min_date, len(xs) - 1, xs)

        return (min_date, len(xs) - 1, xs)

    def _recompute_balance(self, account: str) -> list[tuple[Decimal, Decimal]]:
        (min_date, max_bal_idx, xs) = self.balances[account]

        total = xs[max_bal_idx][1]
        start_idx = max_bal_idx + 1
        for idx, v in enumerate(xs[start_idx:], start=start_idx):
            total += v
            xs[idx] = (v, total)

        self.balances[account] = (min_date, len(xs) - 1, xs)

        return xs

    def check_bassertions(self) -> list[BAssertionFail]:
        err = []
        for ba in self.bassertions:
            actual_balance = self.balance(ba.account, ba.date, ba.include_children)
            diff = ba.balance - actual_balance
            if diff != Decimal("0"):
                err.append(BAssertionFail(bassertion=ba, actual_balance=actual_balance))
        return err

    def balance(self, account: str, date: date, include_children: bool = True) -> Decimal:
        (min_date, max_bal_idx, xs) = self.balances[account]
        if xs is None:
            (min_date, max_bal_idx, xs) = self._init_balance(account)

        if min_date is None or date < min_date:
            total = Decimal("0")
        else:
            idx = (date - min_date).days
            if idx >= len(xs):
                idx = len(xs) - 1
            if idx > max_bal_idx:
                xs = self._recompute_balance(account)
            total = xs[idx][1]

        if include_children:
            for c in self.accounts_graph.successors(account):
                total += self.balance(c, date, include_children=True)
        return total

    def flow(self, account: str, date: date, include_children: bool = True) -> Decimal:
        (min_date, _, xs) = self.balances[account]
        if xs is None:
            (min_date, _, xs) = self._init_balance(account)

        if min_date is None or date < min_date:
            total = Decimal("0")
        else:
            idx = (date - min_date).days
            if idx >= len(xs):
                total = Decimal("0")
            else:
                total = xs[idx][0]
        if include_children:
            for c in self.accounts_graph.successors(account):
                total += self.flow(c, date, include_children=True)
        return total

    def root(self, account: str) -> Account:
        """
        Return the root account of account.
        """
        return self.accounts_graph.nodes[account]["root"]

    def parents(self, account: str) -> list[Account]:
        """
        Return a list of the parents of account from immediate parent to root.
        """
        parents = []
        while account:
            account = self.accounts_graph.nodes[account]["account"].parent
            if account:
                parents.append(self.accounts_graph.nodes[account]["account"])
        return parents

    def children(self, account: str) -> list[Account]:
        """
        Return a list of the immediate children of account.
        """
        return [self.accounts_graph.nodes[c]["account"]
                for c in self.accounts_graph.successors(account)]

    def descendants(self, account: str) -> list[Account]:
        """
        Return a list of the descendants of account.
        Children, children of children, etc.
        """
        return [self.accounts_graph.nodes[c]["account"]
                for c in nx.descendants(self.accounts_graph, account)]

    def accounts_extra(self, accounts: list[Account] = None,
                       extra: AccountExtraTags = None) -> list[Account]:
        """
        Add extra information to accounts.
        If accounts is None, return a copy of self.accounts with extra information.
        If extra is None, use the default extra information.
        """
        if accounts is None:
            accounts = [a.copy() for a in self.accounts]
        if extra is None:
            extra = AccountExtraTags()

        if extra.depth:
            for a in accounts:
                a[extra.depth_tag] = (self.accounts_graph.nodes[a.name]["depth"] +
                                      extra.depth_start)
        if extra.hierarchy:
            max_depth = nx.dag_longest_path_length(self.accounts_graph) + 1
            for a in accounts:
                parents = [a] + self.parents(a.name)
                parents.reverse()
                for i in range(max_depth):
                    if i < len(parents):
                        x = parents[i].name
                    else:
                        x = None
                    a[extra.hierarchy_tag_format.format(i + extra.depth_start)] = x

        return accounts

    def postings_extra(self, ps: list[Posting] = None, today: date = None,
                       extra: PostingExtraTags = None) -> list[Posting]:
        """
        Add extra information to postings.
        If ps is None, return a copy of self.postings with extra information.
        If today is None, use the current date.
        If extra is None, use the default extra information.
        """
        if ps is None:
            ps = [t.copy() for t in self.postings]
            ps_by_id = self.postings_by_txn
        else:
            ps_by_id = defaultdict(list)
            for p in ps:
                ps_by_id[p.txn].append(p)
        if today is None:
            today = date.today()
        if extra is None:
            extra = PostingExtraTags()
        if extra.account_tags:
            accs = self.accounts_extra(extra=extra.account_tags_extra)
            accs_extra_by_name = {a.name: a for a in accs}
        ffm = extra.first_fiscal_month
        for p in ps:
            if extra.account_tags:
                d = accs_extra_by_name[p.account]
                p.update(d._data)
                del p["Name"]  # Already in the account field
            if extra.future_date:
                p[extra.future_date_tag] = p.date > today
            if extra.last_x_days:
                dt = p.date
                for x in extra.last_x_days:
                    p[extra.last_x_days_tag_format.format(x)] = dt > today - timedelta(days=x)
            if extra.year:
                p[extra.year_tag] = p.date.year
            if extra.month:
                p[extra.month_tag] = p.date.month
            if extra.txn_accounts:
                txn_id = p.txn
                p[extra.txn_accounts_tag] = sorted({x.account
                                                    for x in ps_by_id[txn_id]})
                if extra.txn_accounts_as_str:
                    p[extra.txn_accounts_tag] = (extra
                                                 .txn_accounts_join
                                                 .join(p[extra.txn_accounts_tag]))

            if extra.fiscal_year:
                if ffm == 1 or p.date.month < ffm:
                    p[extra.fiscal_year_tag] = p.date.year
                else:
                    p[extra.fiscal_year_tag] = p.date.year + 1
            if extra.fiscal_month:
                p[extra.fiscal_month_tag] = ((p.date.month - ffm) % 12) + 1
        return ps

    def fingerprints(self, tags: list[str] = None) -> dict[tuple, int]:
        d = {}
        for p in self.postings:
            x = p.fingerprint(tags)
            if x not in d:
                d[x] = 1
            else:
                d[x] += 1
        return d

    def next_txn_id(self) -> int:
        """
        Return the next available txn id. All numbers from this id and up are
        available for new txns.
        """
        return max(self.postings_by_txn.keys(), default=0) + 1

    @classmethod
    def from_csv(cls, accounts: str, postings: Union[str, list[str]], bassertions: str = None,
                 encoding: str = "utf-8", **dictreader_args) -> 'Journal':
        with open(accounts, "r", encoding=encoding) as f:
            accounts = [Account.from_dict(x) for x in csv.DictReader(f, **dictreader_args)]

        ps = []
        if isinstance(postings, str):
            postings = [postings]
        for f in postings:
            with open(f, "r", encoding=encoding) as f:
                ps.extend([Posting.from_dict(x) for x in csv.DictReader(f, **dictreader_args)])

        if bassertions is None:
            bas = []
        else:
            with open(bassertions, "r", encoding=encoding) as f:
                bas = [BAssertion.from_dict(x) for x in csv.DictReader(f, **dictreader_args)]
        return cls(accounts, ps, bas)

    @classmethod
    def from_dicts(cls, accounts: list[dict], postings: list[dict],
                   bassertions: list[dict] = None) -> 'Journal':
        if bassertions is None:
            bassertions = []
        return cls([Account.from_dict(x) for x in accounts],
                   [Posting.from_dict(x) for x in postings],
                   [BAssertion.from_dict(x) for x in bassertions])


def find_faulty_postings(j: Journal, fail: BAssertionFail,
                         days_limit: int = 7) -> Union[list[Posting], None]:
    acc = fail.bassertion.account
    ps = j.postings_by_acc[acc]
    if fail.bassertion.include_children:
        for c in j.descendants(acc):
            ps.extend(j.postings_by_acc[c])
    dt = fail.bassertion.date
    ps = [t for t in ps if t.date <= dt and t.date >= dt - timedelta(days=days_limit)]
    ps.sort(key=lambda t: t.date, reverse=True)
    subset = subset_sum([p.amount for p in ps], -fail.diff())
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
