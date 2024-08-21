from datetime import date
import polars as pl
from brightsidebudget import Journal
import brightsidebudget.report as r


def test_add_year_column():
    df = pl.DataFrame({
        "Date": [
            "2024-01-01",
            "2021-02-01",
            "2023-03-01"
        ]}, schema={"Date": pl.Date})
    expected = pl.DataFrame({
        "Date": [
            "2024-01-01",
            "2021-02-01",
            "2023-03-01"
        ],
        "Year": [2024, 2021, 2023]
    }, schema={"Date": pl.Date, "Year": pl.Int32})
    result = r.add_year_column(df)
    assert result.equals(expected)


def test_add_month_column():
    df = pl.DataFrame({
        "Date": [
            "2024-01-01",
            "2021-02-01",
            "2023-03-01"
        ]}, schema={"Date": pl.Date})
    expected = pl.DataFrame({
        "Date": [
            "2024-01-01",
            "2021-02-01",
            "2023-03-01"
        ],
        "Month": ["Jan", "Feb", "Mar"]
    }, schema={"Date": pl.Date, "Month": pl.Utf8})
    result = r.add_month_column(df, month_type="short")
    assert result.equals(expected)

    result = r.add_month_column(df, month_type="long")
    expected = expected.with_columns(
        pl.Series(["January", "February", "March"], dtype=pl.Utf8).alias("Month")
    )
    assert result.equals(expected)

    result = r.add_month_column(df, month_type="number")
    expected = expected.with_columns(
        pl.Series([1, 2, 3], dtype=pl.Int32).alias("Month")
    )
    assert result.equals(expected)


def test_add_year_month_column():
    df = pl.DataFrame({
        "Date": [
            "2024-01-01",
            "2021-02-01",
            "2023-03-01"
        ]}, schema={"Date": pl.Date})
    expected = pl.DataFrame({
        "Date": [
            "2024-01-01",
            "2021-02-01",
            "2023-03-01"
        ],
        "Year-Month": ["2024-01", "2021-02", "2023-03"]
    }, schema={"Date": pl.Date, "Year-Month": pl.Utf8})
    result = r.add_year_month_column(df)
    assert result.equals(expected)


def test_add_fiscal_year_column():
    df = pl.DataFrame({
        "Date": [
            "2024-01-01",
            "2021-02-01",
            "2023-03-01",
            "2023-04-30",
            "2023-12-31"
        ]}, schema={"Date": pl.Date})
    expected = pl.DataFrame({
        "Date": [
            "2024-01-01",
            "2021-02-01",
            "2023-03-01",
            "2023-04-30",
            "2023-12-31"
        ],
        "Fiscal Year": [2024, 2021, 2023, 2024, 2024]
    }, schema={"Date": pl.Date, "Fiscal Year": pl.Int32})
    result = r.add_fiscal_year_column(df, first_fiscal_month=4)
    assert result.equals(expected)

    expected = expected.with_columns(
        pl.Series([2024, 2021, 2023, 2023, 2023], dtype=pl.Int32).alias("Fiscal Year")
    )
    result = r.add_fiscal_year_column(df, first_fiscal_month=1)
    assert result.equals(expected)


def test_add_fiscal_month_column():
    df = pl.DataFrame({
        "Date": [
            "2024-01-01",
            "2021-02-01",
            "2023-03-01",
            "2023-04-30",
            "2023-12-31"
        ]}, schema={"Date": pl.Date})
    expected = pl.DataFrame({
        "Date": [
            "2024-01-01",
            "2021-02-01",
            "2023-03-01",
            "2023-04-30",
            "2023-12-31"
        ],
        "Fiscal Month": [10, 11, 12, 1, 9]
    }, schema={"Date": pl.Date, "Fiscal Month": pl.Int32})
    result = r.add_fiscal_month_column(df, first_fiscal_month=4)
    assert result.equals(expected)

    expected = expected.with_columns(
        pl.Series([1, 2, 3, 4, 12], dtype=pl.Int32).alias("Fiscal Month")
    )
    result = r.add_fiscal_month_column(df, first_fiscal_month=1)
    assert result.equals(expected)


def test_relative_month_column():
    df = pl.DataFrame({
        "Date": [
            "2023-12-31",
            "2024-01-01",
            "2024-02-01",
            "2024-03-01",
            "2024-04-01",
            "2024-05-01",
        ]}, schema={"Date": pl.Date})
    expected = pl.DataFrame({
        "Date": [
            "2023-12-31",
            "2024-01-01",
            "2024-02-01",
            "2024-03-01",
            "2024-04-01",
            "2024-05-01",
        ],
        "Relative Month": [-2, -1, 0, 1, 2, 3]
    }, schema={"Date": pl.Date, "Relative Month": pl.Int32})
    today = date(2024, 2, 1)
    result = r.add_relative_month_column(df, today=today)
    assert result.equals(expected)


def test_add_txn_accounts_colum():
    df = pl.DataFrame({
        "Txn": [1, 1, 2, 2, 3, 3, 4, 4, 4],
        "Account short name": ["Checking", "Food",
                               "Checking", "Other",
                               "Checking", "Salary",
                               "Checking", "Food", "Food"]
    }, schema={"Txn": pl.Int32, "Account short name": pl.Utf8})
    expected = pl.DataFrame({
        "Txn": [1, 1, 2, 2, 3, 3, 4, 4, 4],
        "Account short name": ["Checking", "Food", "Checking", "Other", "Checking", "Salary",
                               "Checking", "Food", "Food"],
        "Txn Accounts": ["Checking | Food", "Checking | Food",
                         "Checking | Other", "Checking | Other",
                         "Checking | Salary", "Checking | Salary",
                         "Checking | Food", "Checking | Food", "Checking | Food"]
    }, schema={"Txn": pl.Int32, "Account short name": pl.Utf8, "Txn Accounts": pl.Utf8})
    result = r.add_txn_accounts_colum(df)

    assert result.equals(expected)


def test_write_excel(accounts_file, txns_file, tmp_path):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    df = j.to_polars()
    tmp_file = tmp_path / "test.xlsx"
    df.write_excel(tmp_file)
