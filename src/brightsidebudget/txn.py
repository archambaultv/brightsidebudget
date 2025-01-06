import csv
from datetime import date
from pathlib import PosixPath
from typing import Callable, Iterable, Union
from decimal import Decimal
from brightsidebudget.account import QName
from brightsidebudget.tag import HasTags, all_tags, clean_tags


class Posting(HasTags):
    """
    A Posting represents a single entry on an account.
    """
    def __init__(self, *, txnid: int, date: date, acc_qname: Union[QName, str], amount: Decimal,
                 comment: Union[str, None] = None, stmt_desc: Union[str, None] = None,
                 stmt_date: Union[date, None] = None,
                 tags: Union[dict[str, str], None] = None):
        super().__init__(tags)
        self.txnid = txnid
        self.date = date
        self.acc_qname = acc_qname if isinstance(acc_qname, QName) else QName(acc_qname)
        self.amount = amount
        self.comment = comment
        self.stmt_desc = stmt_desc
        self.stmt_date = stmt_date or date

    def __str__(self):
        return f'Posting {self.txnid} {self.date} {self.acc_qname} {self.amount}'

    def __repr__(self):
        return self.__str__()

    def copy(self):
        return Posting(txnid=self.txnid, date=self.date, acc_qname=self.acc_qname,
                       amount=self.amount, comment=self.comment, stmt_desc=self.stmt_desc,
                       stmt_date=self.stmt_date, tags=self.tags.copy())


class Txn():
    """
    A Txn represents a single transaction. It contains a list of Postings that all
    have the same date, same txnid and balance to zero.
    """
    def __init__(self, postings: list[Posting]):
        self.postings = postings
        if not postings:
            raise ValueError('Empty list of postings')
        set_txnid = set(p.txnid for p in self.postings)
        if len(set_txnid) != 1:
            raise ValueError(f'Txn postings must have a unique txnid. Got {set_txnid}')
        if len(self.postings) < 2:
            raise ValueError(f'Txn {self.txnid} must have at least two Posting')
        if len(set(p.date for p in self.postings)) != 1:
            raise ValueError(f'Txn {self.txnid} must have the same date')
        s = sum([p.amount for p in self.postings])
        if s != 0:
            raise ValueError(f'Txn {self.txnid} balance is not zero: {s}')

    def __str__(self):
        return f'Txn {self.date} {self.postings}'

    def __repr__(self):
        return self.__str__()

    @property
    def date(self) -> date:
        return self.postings[0].date

    @property
    def txnid(self) -> int:
        return self.postings[0].txnid

    def copy(self):
        return Txn([p.copy() for p in self.postings])


def txn_from_postings(postings: list[Posting]) -> list[Txn]:
    """
    Create a list of Txn from a list of Posting.
    """
    d: dict[int, list[Posting]] = {}
    for p in postings:
        if p.txnid not in d:
            d[p.txnid] = []
        d[p.txnid].append(p)

    return [Txn(postings=ps) for ps in d.values()]


def load_txns(files: str | list[str], encoding: str = 'utf-8') -> list[Txn]:
    """
    Load transactions from a list of CSV files.
    """
    if isinstance(files, (str, PosixPath)):
        files = [files]

    def empty_is_none(x: str | None) -> str | None:
        return None if x == '' else x

    ps: list[Posting] = []
    for p_file in files:
        with open(p_file, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)
            # No txn,Date,Compte,Montant,Date du relevé,Commentaire,Description du relevé
            for row in reader:
                txn_id = int(row['No txn'])
                dt = date.fromisoformat(row['Date'])
                acc = row['Compte']
                amnt = Decimal(row['Montant'])
                comment = empty_is_none(row.get('Commentaire'))
                stmt_desc = empty_is_none(row.get('Description du relevé'))
                stmt_date = empty_is_none(row.get('Date du relevé'))
                if stmt_date:
                    stmt_date = date.fromisoformat(stmt_date)
                d = row.copy()
                xs = ['No txn', 'Date', 'Compte', 'Montant', 'Date du relevé', 'Commentaire',
                      'Description du relevé']
                clean_tags(d, forbidden=xs, err_ctx=f'{txn_id}')

                p = Posting(txnid=txn_id, date=dt, acc_qname=acc, amount=amnt,
                            stmt_desc=stmt_desc, stmt_date=stmt_date, comment=comment,
                            tags=d)
                ps.append(p)
    return txn_from_postings(ps)


def write_txns(*,
               txns: Iterable[Txn],
               filefunc: str | Callable[[Txn], str],
               encoding="utf8"):
    """
    Write the postings to one or more CSV files.
    """
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
        ps = sorted(t.postings, key=lambda x: x.acc_qname.sort_key)
        file_dict[file].extend(ps)

    for file, ps in file_dict.items():
        with open(file, "w", encoding=encoding) as f:
            writer = csv.writer(f, lineterminator="\n")
            header = ["No txn", "Date", "Compte", "Montant", "Date du relevé", "Commentaire",
                      "Description du relevé"]
            p_tag_keys = all_tags(ps)
            header += p_tag_keys

            writer.writerow(header)
            for p in ps:
                txnid = p.txnid
                name = p.acc_qname._qname
                row = [txnid, p.date, name, p.amount, p.stmt_date, p.comment, p.stmt_desc]
                for k in p_tag_keys:
                    row.append(p.tags.get(k, ''))

                writer.writerow(row)
