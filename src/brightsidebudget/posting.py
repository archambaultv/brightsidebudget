import csv
from datetime import date, datetime
from decimal import Decimal
from typing import Callable
from brightsidebudget.account import Account


class Posting:
    def __init__(self, *, txn_id: int, date: date, account: Account, amount: Decimal | None,
                 comment: str = "", stmt_date: date | None = None,
                 stmt_desc: str = ""):
        for x in [comment, stmt_desc]:
            if x is None:
                x = ""
            x.strip()
        if not txn_id or txn_id <= 0:
            raise ValueError("Transaction ID must be a positive integer")
        self.txn_id = txn_id
        self.date = date
        self.account = account
        self.amount = amount
        self.comment = comment
        self.stmt_date = stmt_date or date
        self.stmt_desc = stmt_desc

    def __str__(self) -> str:
        return f"{self.txn_id} {self.date} {self.account} {self.amount}"

    def to_dict(self) -> dict[str, str]:
        if self.stmt_date == self.date:
            stmt_str = ""
        else:
            stmt_str = str(self.stmt_date)

        return {"No txn": str(self.txn_id), "Date": str(self.date), "Compte": self.account.name,
                "Montant": str(self.amount), "Commentaire": self.comment,
                "Date du relevé": stmt_str,
                "Description du relevé": self.stmt_desc}

    def dedup_key(self) -> tuple[date, str, Decimal, str]:
        return self.date, self.account.name, self.amount, self.stmt_desc

    def sort_key(self) -> tuple[date, int, int]:
        return self.date, self.txn_id, self.account.number

    @classmethod
    def from_dict(cls, row: dict[str, str], accounts: dict[str, Account]) -> 'Posting':
        dt = datetime.strptime(row["Date"], "%Y-%m-%d").date()
        stmt_dt = row.get("Date du relevé", dt)
        if not stmt_dt:
            stmt_dt = dt
        if isinstance(stmt_dt, str):
            stmt_dt = datetime.strptime(stmt_dt, "%Y-%m-%d").date()

        if not row["Montant"].strip():
            amnt = None
        else:
            amnt = Decimal(row["Montant"])

        acc = accounts[row["Compte"]]

        return cls(txn_id=int(row["No txn"]), date=dt,
                   account=acc, amount=amnt,
                   comment=row["Commentaire"],
                   stmt_date=stmt_dt,
                   stmt_desc=row["Description du relevé"])

    @staticmethod
    def header() -> list[str]:
        return ["No txn", "Date", "Compte", "Montant", "Date du relevé", "Commentaire",
                "Description du relevé"]

    @staticmethod
    def write_postings(ps: list['Posting'], *,
                       filename: str | Callable[['Posting'], str] = "Transactions.csv",
                       renumber: bool = False):
        if not ps:
            return

        if renumber:
            ps = sorted(ps, key=lambda p: p.sort_key())
            i = 1
            current_id = ps[0].txn_id
            ps[0].txn_id = i
            for p in ps[1:]:
                if p.txn_id != current_id:
                    i += 1
                    current_id = p.txn_id
                p.txn_id = i

        if isinstance(filename, str):
            def name_fn(_: Posting) -> str:
                return filename
        else:
            name_fn = filename

        d: dict[str, list[Posting]] = {}
        for p in ps:
            name = name_fn(p)
            if name not in d:
                d[name] = []
            d[name].append(p)
        for name, ps in d.items():
            ps = sorted(ps, key=lambda p: (p.date, p.txn_id))
            with open(name, "w") as file:
                writer = csv.DictWriter(file, fieldnames=Posting.header(), lineterminator="\n")
                writer.writeheader()
                for p in ps:
                    writer.writerow(p.to_dict())

    @staticmethod
    def get_postings(filenames: list[str], accounts: dict[str, Account]) -> list['Posting']:
        ls: list[Posting] = []
        for f in filenames:
            with open(f, "r") as file:
                for row in csv.DictReader(file):
                    ls.append(Posting.from_dict(row, accounts))
        ls.sort(key=lambda p: p.sort_key())
        return ls
