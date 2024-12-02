import csv
from typing import Any, Union
from brightsidebudget.i18n import AccountHeader


class QName():
    """
    QName (qualified name) is a name that uniquely identifies an account. For example,
    "Assets:Checking" is an account that represents a checking account in the
    Assets category.

    They are immutable and hashable.
    """
    def __init__(self, qname: Union[str, list[str]]):
        if isinstance(qname, list):
            if not qname:
                raise ValueError("Empty qname.")
            self._qname = ':'.join(qname)
            self._qlist = qname
        else:
            if not qname:
                raise ValueError("Empty qname.")
            self._qname = qname
            self._qlist = qname.split(':')

        if any([x == "" for x in self._qlist]):
            raise ValueError("Empty element in qname.")

    @property
    def qstr(self) -> str:
        """
        The qualified name as a string.
        """
        return self._qname

    @property
    def qlist(self) -> list[str]:
        """
        The qualified name as a list of name. The list is a new copy.
        """
        return self._qlist.copy()

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

    def is_equal_or_descendant_of(self, qname: Union['QName', str]) -> bool:
        """
        Returns True if this QName is the qname or a descendant.
        """
        if isinstance(qname, str):
            qname = QName(qname)
        return self == qname or self.is_descendant_of(qname)

    def __eq__(self, other) -> bool:
        if isinstance(other, QName):
            return self._qname == other._qname
        return False

    def __hash__(self) -> int:
        return hash(self._qname)

    def __lt__(self, other) -> bool:
        if isinstance(other, QName):
            return self._qlist < other._qlist
        return False

    def __str__(self):
        return self._qname

    def __repr__(self):
        return self.__str__()


class Account():
    """
    An Account represents a single financial entity where transactions occur. It
    is basically a QName with optional tags.
    """
    def __init__(self, *, qname: Union[QName, str],
                 tags: Union[dict[str, str], None] = None):
        if isinstance(qname, str):
            qname = QName(qname)
        self._qname = qname
        self._tags = tags or {}

    @property
    def qname(self) -> QName:
        """
        The qualified name of the account.
        """
        return self._qname

    @qname.setter
    def qname(self, value: Union[QName, str]):
        if isinstance(value, str):
            value = QName(value)
        self._qname = value

    @property
    def tags(self) -> dict[str, str]:
        return self._tags

    def copy(self) -> 'Account':
        return Account(qname=self._qname, tags=self._tags.copy())

    def tag(self, key: str) -> Union[str, None]:
        return self._tags.get(key, None)

    def __str__(self):
        return str(self._qname)

    def __repr__(self):
        return self.__str__()


def load_accounts(accounts: str, encoding: str = "utf8",
                  acc_header: Union[AccountHeader, None] = None) -> list[Account]:
    """
    Load accounts from a CSV file. The file must have a header with the account name
    and optional tags. The account name is the qualified name of the account. The
    tags are optional and are key-value pairs.
    """
    if acc_header is None:
        acc_header = AccountHeader()
    accs = []
    with open(accounts, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f)
        for row in reader:
            qname = row[acc_header.account]
            d = row.copy()
            clean_tags(d, forbidden=acc_header, err_ctx=qname)

            accs.append(Account(qname=qname, tags=d))
    return accs


def clean_tags(tags: dict[str, Any], forbidden: list[str] = None,
               err_ctx: str = ""):
    """
    Remove empty tags from a dictionary.
    """
    if forbidden is None:
        forbidden = []

    for x in forbidden:
        tags.pop(x, None)
    for k, v in list(tags.items()):
        if v is None or (isinstance(v, str) and v.strip() == ""):
            tags.pop(k)
        if isinstance(v, list):
            msg = "Extra columns"
            if err_ctx:
                msg = f"{err_ctx}: {msg}"
            raise ValueError(msg)
