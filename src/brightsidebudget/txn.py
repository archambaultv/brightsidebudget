from collections import defaultdict
from brightsidebudget.bsberror import BSBError
from brightsidebudget.posting import Posting
from brightsidebudget.account import Account


class Txn:
    def __init__(self, postings: list[Posting]):
        self._postings = postings
        self._validate()

    @property
    def postings(self):
        return self._postings

    @property
    def txn_id(self):
        return self.postings[0].txn_id

    @property
    def date(self):
        return self.postings[0].date

    def accounts(self) -> list[Account]:
        return sorted({p.account for p in self.postings}, key=lambda a: a.sort_key())

    def is_1_n(self) -> bool:
        pos = len([p for p in self.postings if p.amount > 0])
        neg = len([p for p in self.postings if p.amount < 0])
        if pos == 1 or neg == 1:
            return True
        else:
            return False

    def has_zero_amount(self) -> bool:
        return any(p.amount == 0 for p in self.postings)

    def is_uncategorized(self) -> bool:
        return any(p.account.type == "Non classé" for p in self.postings)

    @staticmethod
    def from_postings(ps: list['Posting']) -> list['Txn']:
        d: dict[int, list[Posting]] = defaultdict(list)
        for p in ps:
            d[p.txn_id].append(p)
        return [Txn(v) for v in d.values()]

    def _validate(self):
        if not self.postings:
            raise ValueError("Txn must have at least one posting")

        s_txnid = set(p.txn_id for p in self.postings)
        if len(s_txnid) != 1:
            raise ValueError(f"Txn has different txn_ids : {s_txnid}")

        s_date = set(p.date for p in self.postings)
        if len(set(s_date)) != 1:
            raise BSBError(f"Txn {self.txn_id} has different dates : {s_date}")

        pNone = None
        for p in self.postings:
            if p.amount is None:
                if pNone is not None:
                    raise BSBError(f"Txn {self.txn_id} has more than one None amount")
                pNone = p
        s = sum(p.amount for p in self.postings if p.amount is not None)
        if pNone is not None:
            pNone.amount = -s
            s = 0

        if s != 0:
            raise BSBError(f"Txn {self.txn_id} does not balance. Total: {s}")

    def __str__(self):
        ps = "  \n".join(str(p) for p in self.postings)
        return f"Txn {self.txn_id} {self.date}\n  {ps}"

    def __iter__(self):
        return iter(self.postings)

    def __len__(self):
        return len(self.postings)
