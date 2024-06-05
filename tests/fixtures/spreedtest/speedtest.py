import csv
from datetime import date
from decimal import Decimal
import timeit
from brightsidebudget.journal import Journal


def python_csv():
    """As fast as possible, read the CSV files and basic processing."""
    with open('tests/fixtures/spreedtest/accounts.csv', "r") as f:
        rows = list(csv.DictReader(f))
        for row in rows:
            if not isinstance(row["Name"], str):
                raise ValueError("Name must be a string")
            if not isinstance(row["Parent"], (str, type(None))):
                raise ValueError("Parent must be a string or None")
    with open('tests/fixtures/spreedtest/txns.csv', "r") as f:
        rows = list(csv.DictReader(f))
        for row in rows:
            row["Amount"] = Decimal(str(row["Amount"]))
            row["Txn"] = int(row["Txn"])
            row["Date"] = date.fromisoformat(row["Date"])
    with open('tests/fixtures/spreedtest/bassertions.csv', "r") as f:
        rows = list(csv.DictReader(f))
        for row in rows:
            row["Balance"] = Decimal(str(row["Balance"]))
            row["Date"] = date.fromisoformat(row["Date"])


j: Journal = None


def bsb_csv() -> Journal:
    global j
    j = Journal.from_csv('tests/fixtures/spreedtest/accounts.csv',
                         'tests/fixtures/spreedtest/txns.csv',
                         'tests/fixtures/spreedtest/bassertions.csv')


def bsb_check_bassertions():
    j.check_bassertions()


def bsb_postings_extra():
    today = j.postings[-1].date
    j.postings_extra(today=today)


if __name__ == '__main__':
    # Time the python_csv function
    t_cvs = timeit.timeit(python_csv, number=1)
    print(f"python_csv: {t_cvs:.2f} seconds")

    # Time the bsb_csv function
    t_bsb = timeit.timeit(bsb_csv, number=1)
    print(f"bsb_csv: {t_bsb:.2f} seconds, {t_bsb - t_cvs:.2f} seconds slower")

    # Time the bsb_check_bassertions function
    t_bassertions = timeit.timeit(bsb_check_bassertions, number=1)
    print(f"bsb_check_bassertions: {t_bassertions:.2f} seconds")

    # Time the bsb_postings_extra function
    t_extra = timeit.timeit(bsb_postings_extra, number=1)
    print(f"bsb_postings_extra: {t_extra:.2f} seconds")

    print(f"Total bsb time: {t_bsb + t_bassertions + t_extra:.2f} seconds")
