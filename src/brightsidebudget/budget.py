import csv
from datetime import date, datetime, timedelta
from decimal import Decimal
from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY
from dateutil.relativedelta import relativedelta
from brightsidebudget.account import QName, clean_tags
from brightsidebudget.txn import Posting, Txn


class RPosting():
    """
    A RPosting (recurrent posting) is a posting that occurs at regular intervals.
    It is mainly used for budgeting purposes.
    """
    def __init__(self, *, start: date, acc_qname: QName | str, amount: Decimal,
                 comment: str | None = None, tags: dict[str, str] = None,
                 frequency: str | None = None, interval: int | None = None,
                 count: int | None = None, until: date | None = None):
        self.start = start
        self.acc_qname = acc_qname if isinstance(acc_qname, QName) else QName(acc_qname)
        self.amount = amount
        self.comment = comment
        self.tags = tags or {}
        self.frequency = frequency
        if isinstance(self.frequency, str):
            if self.frequency.lower() == "quotidien":
                self.frequency = DAILY
            elif self.frequency.lower() == "hebdomadaire":
                self.frequency = WEEKLY
            elif self.frequency.lower() == "mensuel":
                self.frequency = MONTHLY
            elif self.frequency.lower() == "annuel":
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
            freq = "quotidien"
        elif self.frequency == WEEKLY:
            freq = "hebdomadaire"
        elif self.frequency == MONTHLY:
            freq = "mensuel"
        elif self.frequency == YEARLY:
            freq = "annuel"
        if freq:
            freq = " " + freq
        comment = f" {self.comment}" if self.comment else ""
        s = f'Target {self.start} {self.acc_qname} {self.amount}'
        return s + freq + comment

    def __repr__(self):
        return self.__str__()

    def copy(self):
        return RPosting(start=self.start, acc_qname=self.acc_qname, amount=self.amount,
                        comment=self.comment, tags=self.tags.copy(), frequency=self.frequency,
                        interval=self.interval, count=self.count, until=self.until)


def load_rpostings(rpostings: str, encoding: str = "utf8") -> list[RPosting]:
    """
    Load recurrent postings from a CSV file.
    """

    def empty_is_none(x: str | None) -> str | None:
        return None if x == '' else x

    ts = []
    with open(rpostings, 'r', encoding=encoding) as f:
        reader = csv.DictReader(f)

        for row in reader:
            start = date.fromisoformat(row["Date de début"])
            acc = row["Compte"]
            amount = Decimal(row["Montant"])
            comment = empty_is_none(row.get("Commentaire"))
            frequency = empty_is_none(row.get("Fréquence"))
            interval = empty_is_none(row.get("Intervalle"))
            if interval:
                interval = int(interval)
            count = empty_is_none(row.get("Nombre de fois"))
            if count:
                count = int(count)
            until = empty_is_none(row.get("Date de fin"))
            if until:
                until = date.fromisoformat(until)
            d = row.copy()
            ctx = f"{start} {acc} {amount}"
            xs = ["Compte", "Commentaire", "Montant", "Date de début", "Fréquence",
                  "Intervalle", "Nombre de fois", "Date de fin"]
            clean_tags(d, forbidden=xs, err_ctx=ctx)

            ts.append(RPosting(start=start, acc_qname=acc, amount=amount,
                               comment=comment, frequency=frequency, interval=interval,
                               count=count, until=until, tags=d))
    return ts


class Budget():
    def __init__(self, rpostings: list[RPosting] | None = None):
        self.rpostings = rpostings if rpostings is not None else []

    def add_targets(self, targets: list[RPosting]):
        """
        Adds a list of budget targets to the Budget.
        """
        self.rpostings.extend(targets)

    def budget_txns(self, start_date: date, end_date: date,
                    counterpart: QName | str) -> list[Txn]:
        """
        Generates a list of transactions from the budget targets
        between start_date and end_date. The counterpart account is used to
        balance the transactions.
        """
        if isinstance(counterpart, str):
            counterpart = QName(qname=counterpart)
        id = 1
        txns: list[Txn] = []
        for r in self.rpostings:
            xs = r.postings_between(start=start_date, end=end_date, txnid=id)
            for p in xs:
                p2 = Posting(txnid=p.txnid, date=p.date, acc_qname=counterpart,
                             amount=-p.amount, comment=p.comment,
                             stmt_desc=p.stmt_desc, stmt_date=p.stmt_date,
                             tags=p.tags.copy())
                txns.append(Txn([p, p2]))
            id += len(xs)

        return txns
