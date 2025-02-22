import subprocess
import sys


def print_yellow(message: str, end: str = "\n"):
    print(f"\033[93m{message}\033[0m", end=end)


def print_red(message: str, end: str = "\n"):
    print(f"\033[91m{message}\033[0m", end=end)


def exit_on_error(error: str):
    print_red(error)
    sys.exit(1)


def csv_to_excel(file: str):
    import pandas as pd
    df = pd.read_csv(file)
    df.to_excel(file.replace(".csv", ".xlsx"), index=False)


def check_git_clean():
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            exit_on_error("Error checking git status:", result.stderr)

        if result.stdout.strip():
            exit_on_error("Uncommitted changes detected.")

    except FileNotFoundError:
        exit_on_error("Git is not installed or not found in PATH.")
