import csv
from pathlib import PosixPath
import polars as pl
from datetime import date, timedelta
from decimal import Decimal
from typing import Callable, Union
from brightsidebudget.account import Account, QName, clean_tags, load_accounts
from brightsidebudget.bassertion import BAssertion, load_balances
from brightsidebudget.i18n import AccountHeader, BAssertionHeader, DataframeHeader, \
    TargetHeader, TxnHeader
from brightsidebudget.posting import Posting, RPosting, Txn, load_rpostings, txn_from_postings


class Journal():
    """
    A Journal is a collection of postings that can be used to track the
    financial activities of a person or organization. It also contains a list
    of accounts, balance assertions and budget targets.
    """
    def __init__(self, *,
                 enforce_1_n: bool = False,
                 auto_create_parents: bool = False):
        """
        Creates an empty journal. Use the add_* methods to populate the journal.
        """
        self.enforce_1_n = enforce_1_n
        self.auto_create_parents = auto_create_parents
        self.accounts: list[Account] = []
        self.postings: list[Posting] = []
        self.targets: list[RPosting] = []
        self.bassertions: list[BAssertion] = []
        self._bassertions_set: set[tuple[date, QName]] = set()
        self.txns_dict: dict[int, Txn] = {}
        # _full_qname_dict: A dictionary that maps a full qualified name to an
        # account
        self._full_qname_dict: dict[QName, Account] = {}
        # _short_qname_dict: A dictionary that maps a short qualified name to a
        # list of matching accounts
        self._short_qname_dict: dict[QName, list[Account]] = {}
        self._next_txn_id = 1

    @property
    def next_txn_id(self) -> int:
        return self._next_txn_id

    def txn(self, txnid: int) -> Txn:
        return self.txns_dict[txnid]

    @property
    def txns(self) -> list[Txn]:
        return list(self.txns_dict.values())

    def account(self, qname: Union[QName, str]) -> Account:
        """
        Returns the account with the given qualified name.

        The qualified name can be shortened if it is unique. For example,
        'Assets:Short-term:Checking' can be shortened to 'Checking', provided
        that there is no other account with the same short name.

        In the case that a full qualified name is also the short name of another
        account, the account corresponding to the full qualified name is
        returned. For example, if there are two accounts 'Assets:Foo:Checking'
        and 'Foo:Checking', then account('Foo:Checking') will return
        'Foo:Checking' and not 'Assets:Foo:Checking'.
        """
        if isinstance(qname, str):
            qname = QName(qname=qname)

        if qname in self._full_qname_dict:
            return self._full_qname_dict[qname]
        elif qname in self._short_qname_dict:
            ls = self._short_qname_dict[qname]
            if len(ls) == 1:
                return ls[0]
            raise ValueError(f'Account {qname} is ambiguous')
        else:
            raise ValueError(f'Account {qname} does not exist')

    def is_valid_qname(self, qname: Union[QName, str]) -> bool:
        """
        Returns True if the qualified name uniquely identifies a single account.
        """
        if isinstance(qname, str):
            qname = QName(qname=qname)

        if qname in self._full_qname_dict:
            return True
        elif qname in self._short_qname_dict:
            return len(self._short_qname_dict[qname]) == 1
        else:
            return False

    def short_qname(self, qname: Union[QName, str],
                    min_length: int = 1) -> QName:
        """
        Returns the shortest qualified name that uniquely identifies the
        account. The qname must be a valid qualified name.
        """
        if min_length < 1:
            raise ValueError('min_length must be greater than 0')

        # We try all possible short names starting from shortest to longest
        acc = self.account(qname)
        qlist = acc.qname._qlist
        min_length = min(min_length, len(qlist))
        for i in range(min_length, len(qlist)):
            short_name = QName(qlist[-i:])
            if short_name in self._full_qname_dict:
                continue
            if len(self._short_qname_dict[short_name]) == 1:
                return short_name
        # No short name found
        return acc.qname

    def full_qname(self, qname: Union[QName, str]) -> QName:
        """
        Returns the full qualified name of an account.
        """
        return self.account(qname).qname

    def is_leaf_account(self, qname: Union[QName, str]) -> bool:
        """
        Returns True if the account is a leaf account.
        """
        full_qname = self.full_qname(qname)
        for a in self.accounts:
            if a.qname.is_descendant_of(full_qname):
                return False
        return True

    def add_accounts(self, accounts: list[Account], copy: bool = False):
        """
        Adds a list of accounts to the journal.
        Verifies that the accounts do not already exist and that the immediate
        parent of each account exists.
        """
        if copy:
            accounts = [a.copy() for a in accounts]

        for a in accounts:
            if a.qname in self._full_qname_dict:
                raise ValueError(f'Account {a.qname} already exists')
            # Check immediate parent exists
            parent = a.qname.parent
            if parent and parent not in self._full_qname_dict:
                if self.auto_create_parents:
                    self.add_accounts([Account(qname=parent)], copy=False)
                else:
                    raise ValueError(f'Parent account {parent} does not exist')

            self._full_qname_dict[a.qname] = a
            self.accounts.append(a)
            qlist = a.qname.qlist
            for idx in range(1, len(qlist)):
                short_name = QName(qlist[-idx:])
                if short_name not in self._short_qname_dict:
                    self._short_qname_dict[short_name] = []
                self._short_qname_dict[short_name].append(a)

    def add_txns(self, txns: Union[Txn, list[Txn]],
                 *,
                 copy: bool = False,
                 ignore_txnid: bool = True):
        """
        Adds transactions to the journal.
        The accounts in the postings must exist in the journal.
        The accounts must be leaf accounts.
        """
        if not isinstance(txns, list):
            txns = [txns]

        if copy:
            txns = [t.copy() for t in txns]

        # Validate postings
        id = self._next_txn_id
        for t in txns:
            if self.enforce_1_n and not t.is_1_n:
                msg = f'Txn {t.txnid} must have only one positive or one negative posting'
                raise ValueError(msg)

            for p in t.postings:
                if ignore_txnid:
                    p.txnid = id
                elif p.txnid in self.txns_dict:
                    raise ValueError(f'Transaction {p.txnid} already exists')

                if not self.is_valid_qname(p.acc_qname):
                    msg = f'Txn {p.txnid}: Account {p.acc_qname} does not exist or is ambiguous'
                    raise ValueError(msg)

                # Update to full qname
                p.acc_qname = self.full_qname(p.acc_qname)

                if not self.is_leaf_account(p.acc_qname):
                    raise ValueError(f'Txn {p.txnid}: Account {p.acc_qname} is not a leaf account')

            id += 1

        for t in txns:
            self.txns_dict[t.txnid] = t
            self.postings.extend(t.postings)

        if ignore_txnid:
            self._next_txn_id = id
        else:
            max_id = max((t.txnid for t in txns), default=0)
            self._next_txn_id = max(max_id + 1, self._next_txn_id)

    def add_bassertions(self, bassertions: Union[BAssertion, list[BAssertion]],
                        copy: bool = False):
        """
        Adds a list of balance assertions to the journal.
        The accounts in the balance assertions must exist in the journal.
        The accounts may be leaf accounts or parent accounts.
        """
        if not isinstance(bassertions, list):
            bassertions = [bassertions]

        if copy:
            bassertions = [b.copy() for b in bassertions]

        for b in bassertions:
            if not self.is_valid_qname(b.acc_qname):
                raise ValueError(f'Account {b.acc_qname} does not exist or is ambiguous')

            # Update to full qname
            b.acc_qname = self.full_qname(b.acc_qname)

            # Check for duplicates
            if (b.date, b.acc_qname) in self._bassertions_set:
                raise ValueError(f'BAssertion {b.date} {b.acc_qname} already exists')
            self._bassertions_set.add((b.date, b.acc_qname))

        for b in bassertions:
            self.bassertions.append(b)

    def add_targets(self, targets: list[RPosting], copy: bool = False):
        """
        Adds a list of budget targets to the journal.
        The accounts in the targets must exist in the journal.
        The accounts must be leaf accounts.
        """
        if copy:
            targets = [t.copy() for t in targets]

        for t in targets:
            if not self.is_valid_qname(t.acc_qname):
                raise ValueError(f'Account {t.acc_qname} does not exist or is ambiguous')
            if not self.is_leaf_account(t.acc_qname):
                raise ValueError(f'Account {t.acc_qname} is not a leaf account')

            # Update to full qname
            t.acc_qname = self.full_qname(t.acc_qname)

        for t in targets:
            self.targets.append(t)

    def balance(self, dt: date, qname: Union[QName, str],
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
        full_qname = self.full_qname(qname)
        for p in self.postings:
            if get_date(p) <= dt and p.acc_qname.is_equal_or_descendant_of(full_qname):
                balance += p.amount

        return balance

    def flow(self, start_date: date, end_date: date, qname: Union[QName, str],
             use_stmt_date: bool = False) -> Decimal:
        """
        Returns the flow of an account between two dates (inclusive).
        """
        if start_date > end_date:
            raise ValueError('start_date must be before end_date')
        start_date = start_date - timedelta(days=1)
        return self.balance(end_date, qname, use_stmt_date) - self.balance(start_date, qname,
                                                                           use_stmt_date)

    def budget_txns(self, start_date: date, end_date: date,
                    counterpart: Union[QName, str]) -> list[Txn]:
        """
        Generates a list of transactions from the budget targets
        between start_date and end_date. The counterpart account is used to
        balance the transactions.
        """
        if isinstance(counterpart, str):
            counterpart = QName(qname=counterpart)
        id = self.next_txn_id
        txns: list[Txn] = []
        for t in self.targets:
            xs = t.postings_between(start=start_date, end=end_date, txnid=id)
            for p in xs:
                p2 = Posting(txnid=p.txnid, date=p.date, acc_qname=counterpart,
                             amount=-p.amount, comment=p.comment,
                             stmt_desc=p.stmt_desc, stmt_date=p.stmt_date,
                             tags=p.tags.copy())
                txns.append(Txn([p, p2]))
            id += len(xs)

        self._next_txn_id = id
        return txns

    @classmethod
    def from_csv(cls, accounts: str, postings: Union[str, list[str], None] = None,
                 bassertions: Union[str, None] = None,
                 targets: Union[str, None] = None,
                 *,
                 encoding: str = 'utf-8',
                 enforce_1_n: bool = False,
                 auto_create_parents: bool = False,
                 acc_header: Union[AccountHeader, None] = None,
                 txn_header: Union[TxnHeader, None] = None,
                 bassertion_header: Union[BAssertionHeader, None] = None,
                 target_header: Union[TargetHeader, None] = None):
        """
        Loads a journal from CSV files.
        """
        if postings is None:
            postings = []
        if isinstance(postings, (str, PosixPath)):
            postings = [postings]
        if txn_header is None:
            txn_header = TxnHeader()

        def empty_is_none(x: Union[str, None]) -> Union[str, None]:
            return None if x == '' else x

        j = cls()
        j.enforce_1_n = enforce_1_n
        j.auto_create_parents = auto_create_parents
        accs = load_accounts(accounts, encoding=encoding, acc_header=acc_header)
        j.add_accounts(accs)

        ps: list[Posting] = []
        for p_file in postings:
            with open(p_file, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    txn_id = int(row[txn_header.txn])
                    dt = date.fromisoformat(row[txn_header.date])
                    acc = row[txn_header.account]
                    amnt = Decimal(row[txn_header.amount])
                    comment = empty_is_none(row.get(txn_header.comment))
                    stmt_desc = empty_is_none(row.get(txn_header.stmt_desc))
                    stmt_date = empty_is_none(row.get(txn_header.stmt_date))
                    if stmt_date:
                        stmt_date = date.fromisoformat(stmt_date)
                    d = row.copy()
                    clean_tags(d, forbidden=txn_header, err_ctx=f'{txn_id}')

                    p = Posting(txnid=txn_id, date=dt, acc_qname=acc, amount=amnt,
                                stmt_desc=stmt_desc, stmt_date=stmt_date, comment=comment,
                                tags=d)
                    ps.append(p)
        j.add_txns(txn_from_postings(ps), ignore_txnid=False)

        if bassertions is not None:
            bs = load_balances(bassertions, encoding=encoding, bassertion_header=bassertion_header)
            j.add_bassertions(bs)

        if targets is not None:
            ts = load_rpostings(targets, encoding=encoding, rposting_header=target_header)
            j.add_targets(ts)

        return j

    def failed_bassertions(self, filter_future_date: bool = True,
                           today: Union[date, None] = None) -> list[BAssertion]:
        """
        Returns the list of assertions that do not match the journal balances.
        The stmt_date is used to compute the actual balance.
        """
        if today is None:
            today = date.today()
        ls = []
        bs = sorted(self.bassertions, key=lambda x: x.date)
        acc_balance: dict[QName, Decimal] = {}
        ps_idx = 0
        ps = sorted(self.postings, key=lambda x: x.stmt_date)
        for b in bs:
            if filter_future_date and b.date > today:
                break

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
                if a.is_equal_or_descendant_of(b.acc_qname):
                    actual += m
            if b.balance != actual:
                ls.append(b)
        return ls

    def last_bassertion(self, qname: Union[QName, str]) -> Union[BAssertion, None]:
        """
        Returns the last balance assertion for the account.
        """
        bs = self.account_bassertions(qname)
        if bs:
            return bs[-1]
        else:
            return None

    def account_bassertions(self, qname: Union[QName, str]) -> list[BAssertion]:
        """
        Returns the list of balance assertions for the account, sorted by date.
        """
        if isinstance(qname, str):
            qname = QName(qname=qname)

        full_qname = self.full_qname(qname)
        bs = [b for b in self.bassertions if b.acc_qname == full_qname]
        bs.sort(key=lambda x: x.date)
        return bs

    def find_subset(self, amnt: Decimal,
                    qname: Union[QName, str],
                    start_date: date,
                    end_date: date,
                    use_stmt_date: bool = False) -> Union[list[Posting], None]:
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

        full_qname = self.full_qname(qname)

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
                               accounts: list[Union[QName, str]],
                               counterparts: list[Union[QName, str]],
                               children: list[Union[QName, str, None]] = None,
                               force_zero_txn: bool = False,
                               comment: Union[str, None] = None) -> list[Txn]:
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
            acc_qname = self.full_qname(acc)
            counterpart = self.full_qname(counterpart)
            if child is None:
                child = acc_qname
            else:
                child = self.full_qname(child)
                if not child.is_equal_or_descendant_of(acc_qname):
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
                self.add_txns(t, ignore_txnid=False)
                txns.append(t)
        return txns

    def all_postings_tags(self, ps: Union[list[Posting], None] = None) -> list[str]:
        """
        Returns a list of all tags used in the postings.
        If ps is None, the function uses all the postings in the journal.
        """
        if ps is None:
            ps = self.postings
        return sorted({k for p in ps for k in p.tags.keys()})

    def all_accounts_tags(self, accs: Union[list[Account], None] = None) -> list[str]:
        """
        Returns a list of all tags used in the accounts.
        If accs is None, the function uses all the accounts in the journal.
        """
        if accs is None:
            accs = self.accounts
        return sorted({k for a in accs for k in a.tags.keys()})

    def all_bassertions_tags(self, bassertions: Union[list[BAssertion], None] = None) -> list[str]:
        """
        Returns a list of all tags used in the balance assertions.
        """
        if bassertions is None:
            bassertions = self.bassertions
        return sorted({k for b in self.bassertions for k in b.tags.keys()})

    def to_polars(self,
                  ps: Union[list[Posting], None] = None,
                  *,
                  df_header: Union[DataframeHeader, None] = None,
                  short_qname_length: Union[dict[QName, int], None] = None) -> pl.DataFrame:
        """
        Returns a polars DataFrame with the postings, including all tags from
        both the postings and the accounts. In the case of a tag name conflict,
        the account tag is suffix with '_acc'.

        If `ps` is None, the function uses all the postings in the journal.
        short_qname_lenght: A dictionary that maps a QName to the minimum length

        The default columns are:
            - Txn: Transaction ID
            - Date: Posting date
            - Account: Account full qualified name
            - Account short name: Account short qualified name
            - Account {i}: Account group i, based on the qualified name
            - Amount: Posting amount
            - Comment: Posting comment
            - Stmt date: Statement date
            - Stmt description: Statement description
            - All tags from the postings
            - All tags from the accounts
        """
        if short_qname_length is None:
            short_qname_length = {}
        if df_header is None:
            df_header = DataframeHeader()
        if ps is None:
            ps = self.postings
        known_keys = set(self.all_postings_tags(ps))
        accs_keys = self.all_accounts_tags()
        accs_keys_map = {}
        for k in accs_keys:
            new_key = k
            if new_key in known_keys:
                new_key += '_acc'
                if new_key in known_keys:
                    i = 2
                    new_key2 = new_key + str(i)
                    while new_key2 in known_keys:
                        i += 1
                        new_key2 = new_key + str(i)
                    new_key = new_key2
            known_keys.add(new_key)
            accs_keys_map[k] = new_key

        max_depth = max((a.qname.depth for a in self.accounts), default=0)

        data = []
        for p in ps:
            if p.acc_qname in short_qname_length:
                short_qname = self.short_qname(p.acc_qname, short_qname_length[p.acc_qname])
            else:
                short_qname = self.short_qname(p.acc_qname)
            d = {
                df_header.txn: p.txnid,
                df_header.date: p.date,
                df_header.account: p.acc_qname.qstr,
                df_header.account_short: short_qname.qstr,
                df_header.amount: float(p.amount),
                df_header.comment: p.comment,
                df_header.stmt_date: p.stmt_date,
                df_header.stmt_desc: p.stmt_desc,
                **p.tags
            }
            for i, group in enumerate(p.acc_qname.qlist):
                d[f'{df_header.account} {i + 1}'] = group
            acc = self.account(p.acc_qname)
            for k in accs_keys:
                d[accs_keys_map[k]] = acc.tag(k)
            data.append(d)
        # Define schema
        schema = {
            df_header.txn: pl.UInt32,
            df_header.date: pl.Date,
            df_header.account: pl.Utf8,
            df_header.account_short: pl.Utf8,
            df_header.amount: pl.Float64,
            df_header.comment: pl.Utf8,
            df_header.stmt_date: pl.Date,
            df_header.stmt_desc: pl.Utf8
        }
        for i in range(1, max_depth + 1):
            schema[f'{df_header.account} {i}'] = pl.Utf8
        for k in known_keys:
            schema[k] = pl.Utf8
        return pl.DataFrame(data, schema=schema)

    def write_bassertions(self, *,
                          bassertions: Union[list[BAssertion], None] = None,
                          file: Union[str, PosixPath] = "bassertions.csv",
                          use_short_qname: bool = False,
                          short_qname_length: Union[dict[QName, int], None] = None,
                          bheader: Union[BAssertionHeader, None] = None,
                          encoding="utf8"):
        """
        Write the balance assertions to a CSV file.
        """
        if short_qname_length is None:
            short_qname_length = {}
        if bassertions is None:
            bassertions = self.bassertions
        if bheader is None:
            bheader = BAssertionHeader()

        bassertions = sorted(bassertions, key=lambda x: (x.date, x.acc_qname))

        with open(file, "w", encoding=encoding) as f:
            writer = csv.writer(f, lineterminator="\n")
            header = [bheader.date, bheader.account, bheader.balance]
            b_tag_keys = self.all_bassertions_tags(bassertions)
            header += b_tag_keys
            writer.writerow(header)
            for b in bassertions:
                if use_short_qname:
                    if b.acc_qname in short_qname_length:
                        short = self.short_qname(b.acc_qname, short_qname_length[b.acc_qname])
                    else:
                        short = self.short_qname(b.acc_qname)
                    row = [b.date, short, b.balance]
                else:
                    row = [b.date, b.acc_qname, b.balance]
                for k in b_tag_keys:
                    row.append(b.tag(k))
                writer.writerow(row)

    def write_txns(self, *,
                   txns: Union[list[Txn], None] = None,
                   filefunc: Union[str, Callable[[Txn], str]] = "txns.csv",
                   use_short_qname: bool = False,
                   short_qname_length: Union[dict[QName, int], None] = None,
                   renumber: bool = False,
                   txn_header: Union[TxnHeader, None] = None,
                   encoding="utf8"):
        """
        Write the postings to one or more CSV files.
        """
        if short_qname_length is None:
            short_qname_length = {}
        if txns is None:
            txns = self.txns_dict.values()
        if txn_header is None:
            txn_header = TxnHeader()

        txns = sorted(txns, key=lambda x: (x.date, x.txnid))

        if isinstance(filefunc, (str, PosixPath)):
            filename = filefunc

            def filefunc(_):
                return filename

        file_dict: dict[str, list[Posting]] = {}
        for t in txns:
            file = filefunc(t)
            if file not in file_dict:
                file_dict[file] = []
            ps = sorted(t.postings, key=lambda x: x.acc_qname.qstr)
            file_dict[file].extend(ps)

        if renumber:
            idx = 1
            ids: dict[int, int] = {}
            for t in txns:
                ids[t.txnid] = idx
                idx += 1

        for file, ps in file_dict.items():
            with open(file, "w", encoding=encoding) as f:
                writer = csv.writer(f, lineterminator="\n")
                header = [txn_header.txn, txn_header.date, txn_header.account,
                          txn_header.amount, txn_header.stmt_date, txn_header.comment,
                          txn_header.stmt_desc]
                p_tag_keys = self.all_postings_tags(ps)
                header += p_tag_keys
                writer.writerow(header)
                for p in ps:
                    if renumber:
                        txnid = ids[p.txnid]
                    else:
                        txnid = p.txnid
                    row = [txnid, p.date]
                    if use_short_qname:
                        if p.acc_qname in short_qname_length:
                            short = self.short_qname(p.acc_qname, short_qname_length[p.acc_qname])
                        else:
                            short = self.short_qname(p.acc_qname)
                        row.append(short)
                    else:
                        row.append(p.acc_qname)
                    row += [p.amount, p.stmt_date, p.comment, p.stmt_desc]
                    for k in p_tag_keys:
                        row.append(p.tag(k))
                    writer.writerow(row)

    def write_accounts(self, *,
                       accounts: Union[list[Account], None] = None,
                       file: Union[str, PosixPath] = "accounts.csv",
                       aheader: Union[AccountHeader, None] = None,
                       encoding="utf8"):
        """
        Write the accounts to a CSV file.
        """
        if accounts is None:
            accounts = self.accounts
        if aheader is None:
            aheader = AccountHeader()

        accounts = sorted(accounts, key=lambda x: x.qname.qstr)

        with open(file, "w", encoding=encoding) as f:
            writer = csv.writer(f, lineterminator="\n")
            header = [aheader.account]
            a_tag_keys = self.all_accounts_tags(accounts)
            header += a_tag_keys
            writer.writerow(header)
            for a in accounts:
                row = [a.qname]
                for k in a_tag_keys:
                    row.append(a.tag(k))
                writer.writerow(row)


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
