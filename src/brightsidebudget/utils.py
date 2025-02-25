import subprocess
import sys

from brightsidebudget.bsberror import BSBError


def print_yellow(message: str, end: str = "\n"):
    print(f"\033[93m{message}\033[0m", end=end)


def print_red(message: str, end: str = "\n"):
    print(f"\033[91m{message}\033[0m", end=end)


def catch_bsberror(fn):
    """
    Decorator to catch BSBError and print the error message in red.
    """
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except BSBError as e:
            print_red(e)
            sys.exit(1)

    return wrapper


def csv_to_excel(file: str):
    import csv
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    with open(file, encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            ws.append(row)
    wb.save(file.replace(".csv", ".xlsx"))


def check_git_clean():
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            raise BSBError("Error checking git status:", result.stderr)

        if result.stdout.strip():
            raise BSBError("Uncommitted changes detected.")

    except FileNotFoundError:
        raise BSBError("Git is not installed or not found in PATH.")
