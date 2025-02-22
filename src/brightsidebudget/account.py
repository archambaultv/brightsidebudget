import csv


class Account:
    def __init__(self, *, name: str, type: str, group: str, sub_group: str, number: int):
        for x in [name, type, group, sub_group]:
            x.strip()
        if not name:
            raise ValueError("Account name cannot be empty")
        if not type:
            raise ValueError("Account type cannot be empty")
        if number <= 0 or number >= 6000:
            raise ValueError("Account number must be between 1 and 5999")
        self.name = name
        self.type = type
        self.group = group
        self.sub_group = sub_group
        self.number = number

    def __str__(self):
        return f"{self.name}"

    def to_dict(self) -> dict[str, str]:
        return {"Compte": self.name, "Type": self.type, "Groupe": self.group,
                "Sous-groupe": self.sub_group, "Numéro": str(self.number)}

    def sort_key(self) -> int:
        return self.number

    @staticmethod
    def header() -> list[str]:
        return ["Compte", "Type", "Groupe", "Sous-groupe", "Numéro"]

    @staticmethod
    def write_accounts(accs: list['Account'], *, filename: str = "Comptes.csv"):
        accs = sorted(accs, key=lambda a: a.sort_key())
        with open(filename, "w") as file:
            writer = csv.DictWriter(file, fieldnames=Account.header(), lineterminator="\n")
            writer.writeheader()
            for a in accs:
                writer.writerow(a.to_dict())

    @staticmethod
    def get_accounts(filename: str = "Comptes.csv") -> list['Account']:
        ls = []
        with open(filename, "r") as file:
            for row in csv.DictReader(file):
                a = Account.from_dict(row)
                ls.append(a)
        return ls

    @classmethod
    def from_dict(cls, row: dict[str, str]) -> 'Account':
        return cls(name=row["Compte"], type=row["Type"], group=row["Groupe"],
                   sub_group=row["Sous-groupe"], number=int(row["Numéro"]))
