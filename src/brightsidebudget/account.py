from typing import Union


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
    def qname(self) -> str:
        """
        The qualified name.
        """
        return self._qname

    @property
    def qlist(self) -> list[str]:
        """
        The qualified name as a list of name.
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
        The depth of the qualified name.
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

    def is_descendant_of(self, parent: 'QName') -> bool:
        """
        Returns True if this QName is a descendant of the parent QName.
        """
        if self.depth <= parent.depth:
            # You can't be a descendant if you have fewer or equal elements
            return False
        return self._qlist[:parent.depth] == parent._qlist

    def is_equal_or_descendant_of(self, qname: 'QName') -> bool:
        """
        Returns True if this QName is the qname or a descendant.
        """
        return self == qname or self.is_descendant_of(qname)

    def __eq__(self, other) -> bool:
        if isinstance(other, QName):
            return self._qname == other._qname
        return False

    def __hash__(self) -> int:
        return hash(self._qname)

    def __str__(self):
        return self._qname

    def __repr__(self):
        return self.__str__()


class Account():
    """
    An Account represents a single financial entity where transactions occur.
    It is basically a QName with optional tags.
    """
    def __init__(self, *, qname: Union[QName, str], tags: dict[str, str] = None):
        self._qname = qname if isinstance(qname, QName) else QName(qname)
        self._tags = tags or {}

    @property
    def qname(self) -> QName:
        """
        The qualified name of the account.
        """
        return self._qname

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