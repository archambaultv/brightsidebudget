
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
    Provides 'name' and 'parent' methods for convenience.
    """
    def __init__(self, name: str, parent: str = None, tags: dict = None):
        self._data = tags if tags is not None else {}
        self._data["Name"] = name
        self._data["Parent"] = parent
        self._check_name_parent()

    def name(self):
        return self._data["Name"]

    def parent(self):
        return self._data["Parent"]

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        if key in ["Name", "Parent"]:
            raise ValueError("Cannot delete {key} key")
        del self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __str__(self):
        return f"Account({self.name()})"

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
        Return a shallow copy of the account.
        """
        a = Account.__new__(Account)
        a._data = self._data.copy()
        return a

    def _check_name_parent(self):
        if not isinstance(self._data["Name"], str):
            raise ValueError("Name must be a string")
        if not isinstance(self._data["Parent"], (str, type(None))):
            raise ValueError("Parent must be a string or None")
        if self._data["Parent"] == "":
            self._data["Parent"] = None
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
        a._check_name_parent()
        return a


class Posting(MutableMapping):
    """
    A dictionary-like object that represents a posting.
    The key 'Txn', 'Date', 'Account' and 'Amount' are always present.
    Provides 'txn', 'date', 'account' and 'amount' methods for convenience.
    """
    def __init__(self, txn: int, date: date, account: str, amount: Decimal,
                 tags: dict = None):
        self._data = tags if tags is not None else {}
        self._data["Txn"] = txn
        self._data["Date"] = date
        self._data["Account"] = account
        self._data["Amount"] = amount
        self._cast_txn_date_amount()

    def txn(self):
        return self._data["Txn"]

    def date(self):
        return self._data["Date"]

    def account(self):
        return self._data["Account"]

    def amount(self):
        return self._data["Amount"]

    def __str__(self):
        return f"Posting({self.txn()}, {self.date()}, {self.account()}, {self.amount()})"

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

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
        return tuple([self.date(), self.account(), self.amount()] +
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
        p._cast_txn_date_amount()
        return p

    def _cast_txn_date_amount(self):
        if not isinstance(self._data["Txn"], int):
            self._data["Txn"] = int(self._data["Txn"])
        if not isinstance(self._data["Amount"], Decimal):
            self._data["Amount"] = Decimal(str(self._data["Amount"]))
        if not isinstance(self._data["Date"], date):
            self._data["Date"] = date.fromisoformat(self._data["Date"])


class BAssertion(MutableMapping):
    """
    A dictionary-like object that represents a balance assertion.
    The key 'Date', 'Account', 'Balance' and 'Include children"' are always present.
    Provides 'date', 'account', 'balance' and 'include_children' methods for convenience.
    """
    def __init__(self, dt: date, account: str, balance: Decimal, include_children: bool = True,
                 tags: dict = None):
        self._data = tags if tags is not None else {}
        self._data["Date"] = dt
        self._data["Account"] = account
        self._data["Balance"] = balance
        self._data["Include children"] = include_children
        self._cast_date_amount()

    def date(self):
        return self._data["Date"]

    def account(self):
        return self._data["Account"]

    def balance(self):
        return self._data["Balance"]

    def include_children(self):
        return self._data["Include children"]

    def __str__(self):
        return f"BAssertion({self.date()}, {self.account()}, {self.balance()}, \
                 {self.include_children()})"

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

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
        ba._cast_date_amount()
        return ba

    def _cast_date_amount(self):
        if not isinstance(self._data["Balance"], Decimal):
            self._data["Balance"] = Decimal(str(self._data["Balance"]))
        if not isinstance(self._data["Date"], date):
            self._data["Date"] = date.fromisoformat(self._data["Date"])


class BAssertionFail():
    def __init__(self, bassertion: BAssertion, actual_balance: Decimal):
        self.bassertion = bassertion
        self.actual_balance = actual_balance

    def diff(self) -> Decimal:
        """
        The difference between the expected balance and the actual balance.
        """
        return self.bassertion.balance() - self.actual_balance

    def __str__(self):
        return f"BAssertionFail({self.bassertion}, {self.actual_balance})"

    def error_msg(self):
        s = f"Balance of {self.bassertion.account()} on {self.bassertion.date()} is "
        s += f"{self.actual_balance} instead of {self.bassertion.balance()}. Diff: {self.diff()}"
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
        # Balances is a dict of dicts. The outer dict is indexed by account
        # identifier and the inner dict is indexed by date. The value is a list
        # [flow, balance] where flow is the sum of all postings on that date and
        # balance is the sum of all postings up to that date.
        self.balances: dict[str, dict[date, list[Decimal]]] = None
        self.min_date: date = None
        self.max_date: date = None
        self.bassertions_by_acc: dict[str, list[BAssertion]] = None

        self._init()

    def _init(self):
        # Verify accounts
        seen = set()
        for a in self.accounts:
            if a.name() in seen:
                raise ValueError(f"Duplicate account {a.name()}")
            seen.add(a.name())
        self.accounts_graph = nx.DiGraph()
        for acc in self.accounts:
            self.accounts_graph.add_node(acc.name(), account=acc)
        for acc in self.accounts:
            if acc.parent():
                if acc.parent() not in self.accounts_graph:
                    raise ValueError(f"Unknown parent: {acc.parent()}")
                self.accounts_graph.add_edge(acc.parent(), acc.name())
        if not nx.is_directed_acyclic_graph(self.accounts_graph):
            cycle = nx.find_cycle(self.accounts_graph)
            msg = " -> ".join([x for x, _ in cycle])
            msg = f"{msg} -> {cycle[0][0]}"
            raise ValueError(f"Cycle in accounts: {msg}")
        for p in self.postings:
            if p.account() not in self.accounts_graph:
                raise ValueError(f"Unknown account: {p.account()}")
        for ba in self.bassertions:
            if ba.account() not in self.accounts_graph:
                raise ValueError(f"Unknown account: {ba.account()}")

        # Add useful information to accounts graph
        self.roots = [self.accounts_graph.nodes[n]["account"]
                      for (n, degree) in self.accounts_graph.in_degree
                      if degree == 0]
        for r in self.roots:
            self.accounts_graph.nodes[r.name()]["root"] = r
            for n in nx.descendants(self.accounts_graph, r.name()):
                self.accounts_graph.nodes[n]["root"] = r
        for n in self.accounts_graph.nodes:
            self.accounts_graph.nodes[n]["depth"] = len(nx.ancestors(self.accounts_graph, n))

        # Compute txns_by_id and txns_by_acc
        self.postings_by_txn = {}
        self.postings_by_acc = {acc.name(): [] for acc in self.accounts}
        for p in self.postings:
            if p.txn() not in self.postings_by_txn:
                self.postings_by_txn[p.txn()] = []
            self.postings_by_txn[p.txn()].append(p)
            self.postings_by_acc[p.account()].append(p)

        # Verify txns
        for k, v in self.postings_by_txn.items():
            s = sum([t.amount() for t in v])
            if s != Decimal("0"):
                raise ValueError(f"Txn {k} is not balanced. Sum: {s}")
            dt_count = len({t.date() for t in v})
            if dt_count != 1:
                raise ValueError(f"Txn {k} has {dt_count} dates")

        # Verify bassertions
        seen = set()
        for ba in self.bassertions:
            if (ba.date(), ba.account()) in seen:
                raise ValueError(f"Duplicate bassertion: {ba.date()} {ba.account()}")
            seen.add((ba.date(), ba.account()))

        # Compute balances
        self.min_date = min([t.date() for t in self.postings], default=None)
        self.max_date = max([t.date() for t in self.postings], default=None)
        self.balances = {acc.name(): {} for acc in self.accounts}
        if self.min_date is not None:
            dates = [(self.min_date + timedelta(days=x))
                     for x in range((self.max_date - self.min_date).days + 1)]
            # To make our lives easier, we add all dates to all accounts. Since
            # there is only 365 days in a year and no one keeps 10 000 years of
            # financial records, this is not a big deal. The alternative would be
            # to use a SortedDict
            for acc in self.accounts:
                xs = self.balances[acc.name()]
                for d in dates:
                    xs[d] = [Decimal("0"), Decimal("0")]
            # Compute flow
            for t in self.postings:
                self.balances[t.account()][t.date()][0] += t.amount()
            # Compute balance
            for v in self.balances.values():
                total = Decimal("0")
                for d in dates:
                    total += v[d][0]
                    v[d][1] = total

        # Compute bassertions_by_acc
        self.bassertions_by_acc = {acc.name(): [] for acc in self.accounts}
        for ba in self.bassertions:
            self.bassertions_by_acc[ba.account()].append(ba)

    def check_bassertions(self) -> list[BAssertionFail]:
        err = []
        for ba in self.bassertions:
            actual_balance = self.balance(ba.account(), ba.date(), ba.include_children())
            diff = ba.balance() - actual_balance
            if diff != Decimal("0"):
                err.append(BAssertionFail(bassertion=ba, actual_balance=actual_balance))
        return err

    def auto_balance(self, bassertion: Union[BAssertion, BAssertionFail],
                     balance_with: str) -> list[Posting]:
        """
        Create a pair of postings that balance the account.
        Returns an empty list if the account is already balanced.
        """
        if isinstance(bassertion, BAssertionFail):
            if bassertion.diff() == Decimal("0"):
                return []
            b = bassertion.bassertion
            p1 = Posting(txn=self.next_txn_id(), date=b.date(), account=b.account(),
                         amount=bassertion.diff())
        else:
            actual_balance = self.balance(bassertion.account(), bassertion.date(),
                                          bassertion.include_children())
            diff = bassertion.balance() - actual_balance
            if diff == Decimal("0"):
                return []
            p1 = Posting(txn=self.next_txn_id(), date=bassertion.date(),
                         account=bassertion.account(), amount=diff)
        p2 = Posting(txn=p1.txn(), date=p1.date(), account=balance_with,
                     amount=-p1.amount())
        return [p1, p2]

    def balance(self, account: str, date: date, include_children: bool = True) -> Decimal:
        if self.min_date is None or date < self.min_date:
            return Decimal("0")
        if date > self.max_date:
            date = self.max_date
        total = self.balances[account][date][1]
        if include_children:
            for c in nx.descendants(self.accounts_graph, account):
                total += self.balances[c][date][1]
        return total

    def flow(self, account: str, date: date, include_children: bool = True) -> Decimal:
        if self.min_date is None or date < self.min_date:
            return Decimal("0")
        if date > self.max_date:
            return Decimal("0")
        total = self.balances[account][date][0]
        if include_children:
            for c in nx.descendants(self.accounts_graph, account):
                total += self.balances[c][date][0]
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
            account = self.accounts_graph.nodes[account]["account"].parent()
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
                a[extra.depth_tag] = (self.accounts_graph.nodes[a.name()]["depth"] +
                                      extra.depth_start)
        if extra.hierarchy:
            max_depth = nx.dag_longest_path_length(self.accounts_graph) + 1
            for a in accounts:
                parents = [a] + self.parents(a.name())
                parents.reverse()
                for i in range(max_depth):
                    if i < len(parents):
                        x = parents[i].name()
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
                ps_by_id[p.txn()].append(p)
        if today is None:
            today = date.today()
        if extra is None:
            extra = PostingExtraTags()
        if extra.account_tags:
            accs = self.accounts_extra(extra=extra.account_tags_extra)
            accs_id = {a.name(): a for a in accs}
            for p in ps:
                d = accs_id[p.account()]
                p.update(d)
                del p["Name"]  # Already in the account field
        if extra.future_date:
            for p in ps:
                p[extra.future_date_tag] = p.date() > today
        if extra.last_x_days:
            for p in ps:
                dt = p.date()
                for x in extra.last_x_days:
                    p[extra.last_x_days_tag_format.format(x)] = dt > today - timedelta(days=x)
        if extra.year:
            for p in ps:
                p[extra.year_tag] = p.date().year
        if extra.month:
            for p in ps:
                p[extra.month_tag] = p.date().month
        if extra.txn_accounts:
            for p in ps:
                txn_id = p.txn()
                p[extra.txn_accounts_tag] = sorted({x.account()
                                                    for x in ps_by_id[txn_id]})
                if extra.txn_accounts_as_str:
                    p[extra.txn_accounts_tag] = (extra
                                                 .txn_accounts_join
                                                 .join(p[extra.txn_accounts_tag]))
        ffm = extra.first_fiscal_month
        if extra.fiscal_year:
            for p in ps:
                if p.date().month >= ffm:
                    p[extra.fiscal_year_tag] = p.date().year
                else:
                    p[extra.fiscal_year_tag] = p.date().year - 1
        if extra.fiscal_month:
            for p in ps:
                p[extra.fiscal_month_tag] = ((p.date().month - ffm) % 12) + 1
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
    acc = fail.bassertion.account()
    ps = j.postings_by_acc[acc]
    if fail.bassertion.include_children():
        for c in j.descendants(acc):
            ps.extend(j.postings_by_acc[c])
    dt = fail.bassertion.date()
    ps = [t for t in ps if t.date() <= dt and t.date() >= dt - timedelta(days=days_limit)]
    ps.sort(key=lambda t: t.date(), reverse=True)
    subset = subset_sum([p.amount() for p in ps], -fail.diff())
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
