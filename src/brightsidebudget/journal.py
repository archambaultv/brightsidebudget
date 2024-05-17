
import csv
import networkx as nx
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Collection, Union
from pydantic import BaseModel, Field


Tags = dict[str, Any]


def mk_tags(d: dict, reserved: Collection[str]) -> Tags:
    tags = {}
    for k, v in d.items():
        if k not in reserved:
            tags[k] = v
    return tags


class Account(BaseModel):
    identifier: str = Field(min_length=1)
    parent: Union[str, None] = Field(min_length=1)
    tags: Tags = Field(default_factory=dict)

    def __str__(self):
        return f"Account({self.identifier}, {self.parent})"

    @classmethod
    def from_dict(cls, d: dict) -> 'Account':
        if "Account" not in d:
            raise ValueError("Missing 'Account' key in account dict")
        p = d.get("Parent", None)
        if p == "":
            p = None
        return cls(identifier=d["Account"],
                   parent=p,
                   tags=mk_tags(d, {"Account", "Parent"}))

    def to_dict(self) -> dict:
        return {"Account": self.identifier, "Parent": self.parent, **self.tags}

    def copy(self) -> 'Account':
        """
        Return a copy of the account. Makes a shallow copy of tags.
        """
        return Account(identifier=self.identifier, parent=self.parent, tags=self.tags.copy())


class Posting(BaseModel):
    txn: int = Field(ge=1)
    date: date
    account: str = Field(min_length=1)
    amount: Decimal
    tags: Tags = Field(default_factory=dict)

    def __str__(self):
        return f"Posting({self.txn}, {self.date}, {self.account}, {self.amount})"

    @classmethod
    def from_dict(cls, d: dict) -> 'Posting':
        for k in ["Txn", "Date", "Account", "Amount"]:
            if k not in d:
                raise ValueError(f"Missing '{k}' key in posting dict")
        return cls(txn=d["Txn"], date=d["Date"],
                   account=d["Account"], amount=d["Amount"],
                   tags=mk_tags(d, {"Txn", "Date", "Account", "Amount"}))

    def to_dict(self) -> dict:
        return {"Txn": self.txn, "Date": self.date, "Account": self.account,
                "Amount": self.amount, **self.tags}

    def copy(self) -> 'Posting':
        """
        Return a copy of the posting. Makes a shallow copy of tags.
        """
        return Posting(txn=self.txn, date=self.date, account=self.account,
                       amount=self.amount, tags=self.tags.copy())

    def fingerprint(self, tags: list[str] = None) -> tuple:
        if tags is None:
            tags = []
        return (self.date, self.account, self.amount) + tuple(self.tags[k] for k in tags)


class BAssertion(BaseModel):
    date: date
    account: str = Field(min_length=1)
    balance: Decimal
    include_children: bool = Field(default=True)
    tags: Tags = Field(default_factory=dict)

    def __str__(self):
        return f"BAssertion({self.date}, {self.account}, {self.balance}, {self.include_children})"

    @classmethod
    def from_dict(cls, d: dict) -> 'BAssertion':
        for k in ["Date", "Account", "Balance"]:
            if k not in d:
                raise ValueError(f"Missing '{k}' key in bassertion dict")
        return cls(date=d["Date"], account=d["Account"],
                   balance=d["Balance"], include_children=d.get("Include children", True),
                   tags=mk_tags(d, {"Date", "Account", "Balance", "Include children"}))

    def to_dict(self) -> dict:
        return {"Date": self.date, "Account": self.account,
                "Balance": self.balance, "Include children": self.include_children, **self.tags}

    def copy(self) -> 'BAssertion':
        """
        Return a copy of the bassertion. Makes a shallow copy of tags.
        """
        return BAssertion(date=self.date, account=self.account,
                          balance=self.balance, include_children=self.include_children,
                          tags=self.tags.copy())


class BAssertionFail(BaseModel):
    bassertion: BAssertion
    actual_balance: Decimal

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
            if a.identifier in seen:
                raise ValueError(f"Duplicate account {a.identifier}")
            seen.add(a.identifier)
        self.accounts_graph = nx.DiGraph()
        for acc in self.accounts:
            self.accounts_graph.add_node(acc.identifier, account=acc)
        for acc in self.accounts:
            if acc.parent:
                if acc.parent not in self.accounts_graph:
                    raise ValueError(f"Unknown parent: {acc.parent}")
                self.accounts_graph.add_edge(acc.parent, acc.identifier)
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
            self.accounts_graph.nodes[r.identifier]["root"] = r
            for n in nx.descendants(self.accounts_graph, r.identifier):
                self.accounts_graph.nodes[n]["root"] = r
        for n in self.accounts_graph.nodes:
            self.accounts_graph.nodes[n]["depth"] = len(nx.ancestors(self.accounts_graph, n))

        # Compute txns_by_id and txns_by_acc
        self.postings_by_txn = {}
        self.postings_by_acc = {acc.identifier: [] for acc in self.accounts}
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

        # Compute balances
        self.min_date = min([t.date for t in self.postings], default=None)
        self.max_date = max([t.date for t in self.postings], default=None)
        self.balances = {acc.identifier: {} for acc in self.accounts}
        if self.min_date is not None:
            dates = [(self.min_date + timedelta(days=x))
                     for x in range((self.max_date - self.min_date).days + 1)]
            # To make our lives easier, we add all dates to all accounts. Since
            # there is only 365 days in a year and no one keeps 10 000 years of
            # financial records, this is not a big deal. The alternative would be
            # to use a SortedDict
            for acc in self.accounts:
                xs = self.balances[acc.identifier]
                for d in dates:
                    xs[d] = [Decimal("0"), Decimal("0")]
            # Compute flow
            for t in self.postings:
                self.balances[t.account][t.date][0] += t.amount
            # Compute balance
            for v in self.balances.values():
                total = Decimal("0")
                for d in dates:
                    total += v[d][0]
                    v[d][1] = total

        # Compute bassertions_by_acc
        self.bassertions_by_acc = {acc.identifier: [] for acc in self.accounts}
        for ba in self.bassertions:
            self.bassertions_by_acc[ba.account].append(ba)

    def check_bassertions(self) -> list[BAssertionFail]:
        err = []
        for ba in self.bassertions:
            actual_balance = self.balance(ba.account, ba.date, ba.include_children)
            diff = ba.balance - actual_balance
            if diff != Decimal("0"):
                err.append(BAssertionFail(bassertion=ba, actual_balance=actual_balance))
        return err

    def balance(self, account: str, date: date, include_children: bool = True) -> Decimal:
        if date < self.min_date:
            return Decimal("0")
        if date > self.max_date:
            date = self.max_date
        total = self.balances[account][date][1]
        if include_children:
            for c in nx.descendants(self.accounts_graph, account):
                total += self.balances[c][date][1]
        return total

    def flow(self, account: str, date: date, include_children: bool = True) -> Decimal:
        if date < self.min_date:
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
                a.tags[extra.depth_tag] = (self.accounts_graph.nodes[a.identifier]["depth"] +
                                           extra.depth_start)
        if extra.hierarchy:
            max_depth = nx.dag_longest_path_length(self.accounts_graph) + 1
            for a in accounts:
                parents = [a] + self.parents(a.identifier)
                parents.reverse()
                for i in range(max_depth):
                    if i < len(parents):
                        x = parents[i].identifier
                    else:
                        x = None
                    a.tags[extra.hierarchy_tag_format.format(i + extra.depth_start)] = x

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
        if today is None:
            today = date.today()
        if extra is None:
            extra = PostingExtraTags()
        if extra.account_tags:
            accs = self.accounts_extra(extra=extra.account_tags_extra)
            accs_id = {a.identifier: a for a in accs}
            for p in ps:
                d = accs_id[p.account].to_dict()
                del d["Account"]  # Already in the account field
                p.tags.update(d)
        if extra.future_date:
            for p in ps:
                p.tags[extra.future_date_tag] = p.date > today
        if extra.last_x_days:
            for p in ps:
                dt = p.date
                for x in extra.last_x_days:
                    p.tags[extra.last_x_days_tag_format.format(x)] = dt > today - timedelta(days=x)
        if extra.year:
            for p in ps:
                p.tags[extra.year_tag] = p.date.year
        if extra.month:
            for p in ps:
                p.tags[extra.month_tag] = p.date.month
        if extra.txn_accounts:
            for p in ps:
                txn_id = p.txn
                p.tags[extra.txn_accounts_tag] = sorted({x.account
                                                         for x in self.postings_by_txn[txn_id]})
                if extra.txn_accounts_as_str:
                    p.tags[extra.txn_accounts_tag] = (extra
                                                      .txn_accounts_join
                                                      .join(p.tags[extra.txn_accounts_tag]))
        ffm = extra.first_fiscal_month
        if extra.fiscal_year:
            for p in ps:
                if p.date.month >= ffm:
                    p.tags[extra.fiscal_year_tag] = p.date.year
                else:
                    p.tags[extra.fiscal_year_tag] = p.date.year - 1
        if extra.fiscal_month:
            for p in ps:
                p.tags[extra.fiscal_month_tag] = ((p.date.month - ffm) % 12) + 1
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
