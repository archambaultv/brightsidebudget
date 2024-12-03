import csv
from datetime import date, datetime, timedelta
from typing import Union
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY
from brightsidebudget.account import QName, clean_tags
from brightsidebudget.i18n import TargetHeader


class Posting():
    """
    A Posting represents a single entry on an account.
    """
    def __init__(self, *, txnid: int, date: date, acc_qname: Union[QName, str], amount: Decimal,
                 comment: Union[str, None] = None, stmt_desc: Union[str, None] = None,
                 stmt_date: Union[date, None] = None,
                 tags: Union[dict[str, str], None] = None):
        self.txnid = txnid
        self.date = date
        self._acc_qname = acc_qname if isinstance(acc_qname, QName) else QName(acc_qname)
        self.amount = amount
        self.comment = comment
        self.stmt_desc = stmt_desc
        self.stmt_date = stmt_date or date
        self.tags = tags or {}

    @property
    def acc_qname(self) -> QName:
        return self._acc_qname

    @acc_qname.setter
    def acc_qname(self, value: Union[QName, str]):
        if isinstance(value, QName):
            self._acc_qname = value
        else:
            self._acc_qname = QName(value)

    def tag(self, key: str) -> Union[str, None]:
        return self.tags.get(key, None)

    def copy(self) -> 'Posting':
        return Posting(txnid=self.txnid, date=self.date, acc_qname=self._acc_qname,
                       amount=self.amount,
                       comment=self.comment, stmt_desc=self.stmt_desc, stmt_date=self.stmt_date,
                       tags=self.tags.copy())

    def __str__(self):
        return f'Posting {self.txnid} {self.date} {self.acc_qname} {self.amount}'

    def __repr__(self):
        return self.__str__()


class Txn():
    """
    A Txn represents a single transaction. It contains a list of Postings that all
    have the same date, same txnid and balance to zero.
    """
    def __init__(self, postings: list[Posting], enforce_1_n: bool = False):
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
        if enforce_1_n and not self.is_1_n:
            msg = f'Txn {self.txnid} must have only one positive or one negative posting'
            raise ValueError(msg)

    def __str__(self):
        return f'Txn {self.date} {self.postings}'

    def __repr__(self):
        return self.__str__()

    def copy(self) -> 'Txn':
        return Txn(date=self.date, postings=[p.copy() for p in self.postings])

    @property
    def date(self) -> date:
        return self.postings[0].date

    @property
    def txnid(self) -> int:
        return self.postings[0].txnid

    @property
    def is_1_n(self) -> bool:
        nbPos = [p for p in self.postings if p.amount > 0]
        nbNeg = [p for p in self.postings if p.amount < 0]
        if len(nbPos) > 1 and len(nbNeg) > 1:
            return False
        return True

    def simplify(self) -> Union['Txn', None]:
        """
        Simplify the transaction by removing zero amount postings
        and merging postings with the same account and same statement date.

        Metadata are discarded.
        """
        d_sum: dict[tuple[QName, date], Decimal] = {}
        for p in self.postings:
            key = (p.acc_qname, p.stmt_date)
            if key not in d_sum:
                d_sum[key] = Decimal(0)
            d_sum[key] += p.amount

        new_postings = []
        for (acc, stmt_date), amount in d_sum.items():
            if amount == 0:
                continue
            p = Posting(txnid=self.txnid, date=self.date, acc_qname=acc, amount=amount,
                        comment=None, stmt_desc=None,
                        stmt_date=stmt_date, tags=None)
            new_postings.append(p)
        if not new_postings:
            return None
        return Txn(postings=new_postings, enforce_1_n=self.is_1_n)


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


class RPosting():
    """
    A RPosting (recurrent posting) is a posting that occurs at regular intervals.
    It is mainly used for budgeting purposes.
    """
    def __init__(self, *, start: date, acc_qname: Union[QName, str], amount: Decimal,
                 comment: Union[str, None] = None, tags: dict[str, str] = None,
                 frequency: Union[str, None] = None, interval: Union[int, None] = None,
                 count: Union[int, None] = None, until: Union[date, None] = None):
        self.start = start
        self._acc_qname = acc_qname if isinstance(acc_qname, QName) else QName(acc_qname)
        self.amount = amount
        self.comment = comment
        self.tags = tags or {}
        self.frequency = frequency
        if isinstance(self.frequency, str):
            if self.frequency.lower() == "daily":
                self.frequency = DAILY
            elif self.frequency.lower() == "weekly":
                self.frequency = WEEKLY
            elif self.frequency.lower() == "monthly":
                self.frequency = MONTHLY
            elif self.frequency.lower() == "yearly":
                self.frequency = YEARLY
            else:
                raise ValueError(f'Invalid frequency {self.frequency}')
        self.interval = interval
        if self.frequency is not None and self.interval is None:
            raise ValueError('Interval must be set when frequency is set')
        self.count = count
        self.until = until
        if self.count is not None and self.until is not None:
            raise ValueError(f'Count ({self.count}) and until ({self.until}) \
                             cannot be set at the same time')

        # Build rrule
        s = datetime(self.start.year, self.start.month, self.start.day)
        if self.frequency is None:
            r = rrule(MONTHLY, dtstart=s, count=1)
        elif self.until:
            r = rrule(self.frequency, dtstart=s, interval=self.interval, until=self.until)
        elif self.count:
            r = rrule(self.frequency, dtstart=s, interval=self.interval, count=self.count)
        else:
            r = rrule(self.frequency, dtstart=s, interval=self.interval)
        self._rrule = r

    @property
    def acc_qname(self) -> QName:
        return self._acc_qname

    @acc_qname.setter
    def acc_qname(self, value: Union[QName, str]):
        if isinstance(value, QName):
            self._acc_qname = value
        else:
            self._acc_qname = QName(value)

    def postings_for_month(self, month: date) -> list[Posting]:
        """
        Return the total amount for the month.
        """
        sd = date(month.year, month.month, 1)
        ed = sd + relativedelta(months=1) - timedelta(days=1)
        return self.postings_between(sd, ed)

    def postings_for_year(self, year: int) -> list[Posting]:
        """
        Return the total amount for the year.
        """
        sd = date(year, 1, 1)
        ed = date(year, 12, 31)
        return self.postings_between(sd, ed)

    def postings_between(self, start: date, end: date, txnid: int = 1) -> list[Posting]:
        """
        Return a list of postings for the period [start, end] inclusive.
        """
        ls = []
        sd = datetime(start.year, start.month, start.day)
        ed = datetime(end.year, end.month, end.day)
        for d in self._rrule.between(sd, ed, inc=True):
            p = Posting(txnid=txnid, date=d.date(), acc_qname=self.acc_qname, amount=self.amount,
                        comment=self.comment, tags=self.tags.copy())
            ls.append(p)
            txnid += 1
        return ls

    def __str__(self):
        freq = ""
        if self.frequency == DAILY:
            freq = "daily"
        elif self.frequency == WEEKLY:
            freq = "weekly"
        elif self.frequency == MONTHLY:
            freq = "monthly"
        elif self.frequency == YEARLY:
            freq = "yearly"
        if freq:
            freq = " " + freq
        comment = f" {self.comment}" if self.comment else ""
        s = f'Target {self.start} {self.acc_qname} {self.amount}'
        return s + freq + comment

    def __repr__(self):
        return self.__str__()

    def copy(self) -> 'RPosting':
        return RPosting(start=self.start, acc_qname=self._acc_qname, amount=self.amount,
                        comment=self.comment, tags=self.tags.copy(), frequency=self.frequency,
                        interval=self.interval, count=self.count, until=self.until)


def load_rpostings(rpostings: str, encoding: str = "utf8",
                   rposting_header: Union[TargetHeader, None] = None) -> list[RPosting]:
    """
    Load recurrent postings from a CSV file.
    """
    if rposting_header is None:
        rposting_header = TargetHeader()

    def empty_is_none(x: Union[str, None]) -> Union[str, None]:
        return None if x == '' else x

    ts = []
    with open(rpostings, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f)

        for row in reader:
            start = date.fromisoformat(row[rposting_header.start_date])
            acc = row[rposting_header.account]
            amount = Decimal(row[rposting_header.amount])
            comment = empty_is_none(row.get(rposting_header.comment))
            frequency = empty_is_none(row.get(rposting_header.frequency))
            interval = empty_is_none(row.get(rposting_header.interval))
            if interval:
                interval = int(interval)
            count = empty_is_none(row.get(rposting_header.count))
            if count:
                count = int(count)
            until = empty_is_none(row.get(rposting_header.until))
            if until:
                until = date.fromisoformat(until)
            d = row.copy()
            ctx = f"{start} {acc} {amount}"
            clean_tags(d, forbidden=rposting_header, err_ctx=ctx)

            ts.append(RPosting(start=start, acc_qname=acc, amount=amount,
                               comment=comment, frequency=frequency, interval=interval,
                               count=count, until=until, tags=d))
    return ts
