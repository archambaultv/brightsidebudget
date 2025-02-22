import csv
from datetime import date, datetime
from decimal import Decimal
from brightsidebudget.account import Account


class BAssertion:
    def __init__(self, *, date: date, account: Account, balance: Decimal, comment: str = ""):
        comment.strip()

        self.date = date
        self.account = account
        self.balance = balance
        self.comment = comment

    def to_dict(self) -> dict[str, str]:
        return {"Date": str(self.date), "Compte": self.account.name, "Solde": str(self.balance),
                "Commentaire": self.comment}

    def dedup_key(self) -> tuple[date, str]:
        return self.date, self.account.name

    def sort_key(self) -> tuple[date, int]:
        return self.date, self.account.number

    @staticmethod
    def header() -> list[str]:
        return ["Date", "Compte", "Solde", "Commentaire"]

    @staticmethod
    def write_assertions(bs: list['BAssertion'],
                         filename: str = "Soldes.csv"):
        bs = sorted(bs, key=lambda b: b.sort_key())
        with open(filename, "w") as file:
            writer = csv.DictWriter(file, fieldnames=BAssertion.header(), lineterminator="\n")
            writer.writeheader()
            for b in bs:
                writer.writerow(b.to_dict())

    @staticmethod
    def get_assertions(filename: str, accounts: dict[str, Account]) -> list['BAssertion']:
        bs = []
        with open(filename, "r") as file:
            for row in csv.DictReader(file):
                bs.append(BAssertion.from_dict(row, accounts))

        return bs

    @classmethod
    def from_dict(cls, row: dict[str, str], accounts: dict[str, Account]) -> 'BAssertion':
        dt = datetime.strptime(row["Date"], "%Y-%m-%d").date()
        acc = accounts[row["Compte"]]
        return cls(date=dt, account=acc, balance=Decimal(row["Solde"]),
                   comment=row["Commentaire"])
