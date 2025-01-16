import csv
from pathlib import PosixPath
from typing import Callable, Iterable, Union
from brightsidebudget.tag import all_tags, clean_tags, HasTags


class QName:
    """
    QName (qualified name) is a name that uniquely identifies an account. For example,
    "Assets:Checking" is an account that represents a checking account in the
    Assets category.
    """
    def __init__(self, qname: str | list[str]):
        if isinstance(qname, list):
            if not qname:
                raise ValueError("Empty qname.")
            self._qstr = ':'.join(qname)
            self._qlist = qname
        else:
            if not qname:
                raise ValueError("Empty qname.")
            self._qstr = qname
            self._qlist = qname.split(':')

        if any([x == "" for x in self._qlist]):
            raise ValueError("Empty element in qname.")
        if any([":" in x for x in self._qlist]):
            raise ValueError("Colon in element.")

    @property
    def qstr(self) -> str:
        """
        The qualified name as a string.
        """
        return self._qstr

    @property
    def qlist(self) -> list[str]:
        """
        The qualified name as a list of elements.
        """
        return self._qlist

    @property
    def basename(self) -> str:
        """
        The base name, i.e. the last element of the qualified name.
        """
        return self._qlist[-1]

    @property
    def depth(self) -> int:
        """
        The depth of the qualified name. Equals to the number of elements in the QName.
        """
        return len(self._qlist)

    @property
    def parent(self) -> Union['QName', None]:
        """
        The parent QName.
        """
        if len(self._qlist) == 1:
            return None
        return QName(self._qlist[:-1])

    def is_descendant_of(self, parent: Union['QName', str]) -> bool:
        """
        Returns True if this QName is a descendant of the parent QName.
        """
        if isinstance(parent, str):
            parent = QName(parent)
        if self.depth <= parent.depth:
            # You can't be a descendant if you have fewer or equal elements
            return False
        return self._qlist[:parent.depth] == parent._qlist

    def is_parent_of(self, qname: Union['QName', str]) -> bool:
        """
        Returns True if this QName is a parent of the given QName.
        """
        if isinstance(qname, str):
            qname = QName(qname)
        return qname.is_descendant_of(self)

    @property
    def sort_key(self) -> tuple[int, list[str]]:
        """
        Returns a tuple that can be used for sorting.
        Ensures that the parent comes before the children and that the five
        top accounts come in the proper order. (Actifs, Passifs, Capitaux propres, Revenus,
        Dépenses)
        """
        order = {
            "Actifs": 1,
            "Passifs": 2,
            "Capitaux propres": 3,
            "Revenus": 4,
            "Dépenses": 5
        }
        return order.get(self._qlist[0], 6), self._qlist

    def __eq__(self, other) -> bool:
        if isinstance(other, QName):
            return self._qstr == other._qstr
        return False

    def __hash__(self) -> int:
        return hash(self._qstr)

    def __lt__(self, other) -> bool:
        if isinstance(other, QName):
            return self._qlist < other._qlist
        return False

    def __str__(self):
        return self._qstr

    def __repr__(self):
        return self.__str__()


class Account(HasTags):
    """
    An Account represents a single financial entity where transactions occur. It
    is basically a QName with optional tags.
    """
    def __init__(self, *, qname: QName | str, tags: dict[str, str] | None = None):
        super().__init__(tags)
        if isinstance(qname, str):
            qname = QName(qname)
        self.qname = qname

    def __str__(self):
        return str(self.qname)

    def __repr__(self):
        return self.__str__()

    def copy(self):
        return Account(qname=self.qname, tags=self.tags.copy())


def load_accounts(accounts: str, encoding: str = "utf8") -> list['Account']:
    """
    Load accounts from a CSV file. The file must have a header with the account name
    and optional tags. The account name is the qualified name of the account. The
    tags are optional and are key-value pairs.
    """
    accs = []
    with open(accounts, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f)
        for row in reader:
            qname = row["Compte"]
            d = row.copy()
            clean_tags(d, forbidden=["Compte"], err_ctx=qname)

            accs.append(Account(qname=qname, tags=d))
    return accs


def write_accounts(*,
                   accounts: Iterable[Account],
                   file: str | PosixPath,
                   encoding="utf8"):
    """
    Write the accounts to a CSV file.
    """
    accounts = sorted(accounts, key=lambda x: x.qname.sort_key)

    with open(file, "w", encoding=encoding) as f:
        writer = csv.writer(f, lineterminator="\n")
        header = ["Compte"]
        a_tag_keys = all_tags(accounts)
        header += a_tag_keys
        writer.writerow(header)
        for a in accounts:
            row = [a.qname]
            for k in a_tag_keys:
                row.append(a.tags.get(k, ""))
            writer.writerow(row)


class ChartOfAccounts:
    def __init__(self):
        # _full_qname_dict: A dictionary that maps a full qualified name to an
        # account
        self._full_qname_dict: dict[QName, Account] = {}
        # _short_qname_dict: A dictionary that maps a short qualified name to a
        # list of matching accounts
        self._short_qname_dict: dict[QName, list[Account]] = {}
        self.short_qname_min_length: Callable[[QName], int] = lambda x: 1

    @property
    def accounts(self) -> Iterable[Account]:
        """
        Returns a list of all accounts in the chart of accounts.
        """
        return iter(self._full_qname_dict.values())

    def account(self, qname: QName | str) -> Account:
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

    def is_valid_qname(self, qname: QName | str) -> bool:
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

    def short_qname(self, qname: QName | str) -> QName:
        """
        Returns the shortest qualified name that uniquely identifies the
        account. The qname must be a valid qualified name.
        """

        # We try all possible short names starting from shortest to longest
        acc = self.account(qname)
        qlist = acc.qname.qlist
        min_length = min(max(self.short_qname_min_length(acc.qname), 1), len(qlist))
        for i in range(min_length, len(qlist)):
            short_name = QName(qlist[-i:])
            if short_name in self._full_qname_dict:
                continue
            if len(self._short_qname_dict[short_name]) == 1:
                return short_name
        # No short name found
        return acc.qname

    def full_qname(self, qname: QName | str) -> QName:
        """
        Returns the full qualified name of an account.
        """
        return self.account(qname).qname

    def is_leaf_account(self, qname: QName | str) -> bool:
        """
        Returns True if the account is a leaf account.
        """
        full_qname = self.full_qname(qname)
        for a in self._full_qname_dict.values():
            if a.qname.is_descendant_of(full_qname):
                return False
        return True

    def add_accounts(self, accounts: list[Account]):
        """
        Adds a list of accounts to the journal.
        Verifies that the accounts do not already exist and that the immediate
        parent of each account exists.
        """
        for a in accounts:
            if a.qname in self._full_qname_dict:
                raise ValueError(f'Account {a.qname} already exists')
            # Check immediate parent exists
            parent = a.qname.parent
            if parent and parent not in self._full_qname_dict:
                raise ValueError(f'Parent account {parent} does not exist')

            self._full_qname_dict[a.qname] = a
            qlist = a.qname.qlist
            for idx in range(1, len(qlist)):
                short_name = QName(qlist[-idx:])
                if short_name not in self._short_qname_dict:
                    self._short_qname_dict[short_name] = []
                self._short_qname_dict[short_name].append(a)

    def max_depth(self) -> int:
        """
        Returns the maximum depth of the qualified names in the chart of accounts.
        """
        return max((a.qname.depth for a in self._full_qname_dict.values()), default=0)
