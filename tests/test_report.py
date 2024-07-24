from datetime import date
from dateutil.relativedelta import relativedelta
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


def test_side_by_side():
    df1 = pl.DataFrame({
        "Date": [
            "2024-01-01",
            "2021-02-01",
            "2023-03-01"
        ]}, schema={"Date": pl.Date})
    df2 = pl.DataFrame({
        "Account": [
            "Checking",
            "Saving",
            "Credit card",
            "Food"
        ]}, schema={"Account": pl.Utf8})

    result = r.side_by_side(df1, df2, separator="~")
    df1_lines = []
    df2_lines = []
    for line in result.split("\n"):
        s = line.split("~")
        if s[0].strip():
            df1_lines.append(s[0])
        if s[1].strip():
            df2_lines.append(s[1])
    assert '\n'.join(df1_lines) == str(df1)
    assert '\n'.join(df2_lines) == str(df2)


def test_sort_by():
    df = pl.DataFrame({
        "Account": [
            "Assets",
            "Expenses",
            "Revenue",
            "Other",
            "Liabilities"
        ]
    }, schema={"Account": pl.Utf8})
    expected = pl.DataFrame({
        "Account": [
            "Assets",
            "Liabilities",
            "Revenue",
            "Expenses",
            "Other"
        ]
    }, schema={"Account": pl.Utf8})
    mapping = {
        "Assets": 1,
        "Liabilities": 2,
        "Revenue": 3,
        "Expenses": 4
    }
    result = r.sort_by(df, by="Account", order_mapping=mapping)
    assert result.equals(expected)

    result = r.sort_by(df, by="Account", order_mapping=mapping,
                       descending=True)
    assert result.equals(expected.reverse())


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


def report_df(with_budget: bool = False) -> pl.DataFrame:
    data = []
    for idx in range(24):
        acc_n = idx % 2 + 1
        d1 = {
            "Date": date(2021, 1, 1) + relativedelta(months=idx),
            "Account": f"Assets:Asset {acc_n}",
            "Account 1": "Assets",
            "Account 2": f"Asset {acc_n}",
            "Txn type": "actual",
            "Amount": 100
        }
        d2 = {
            "Date": date(2021, 1, 1) + relativedelta(months=idx),
            "Account": f"Liabilities:Liability {acc_n}",
            "Account 1": "Liabilities",
            "Account 2": f"Liability {acc_n}",
            "Txn type": "actual",
            "Amount": -100
        }
        data.append(d1)
        data.append(d2)

        if with_budget:
            d3 = {
                "Date": date(2021, 1, 1) + relativedelta(months=idx),
                "Account": f"Assets:Asset {acc_n}",
                "Account 1": "Assets",
                "Account 2": f"Asset {acc_n}",
                "Txn type": "budget",
                "Amount": 95
            }
            data.append(d3)

    df = pl.DataFrame(data, schema={"Date": pl.Date, "Account": pl.Utf8, "Amount": pl.Float64,
                                    "Account 1": pl.Utf8, "Account 2": pl.Utf8,
                                    "Txn type": pl.Utf8})
    return df


def test_balance_report():
    df = report_df()
    result = r.balance_report(df, on="Year", index="Account 1")
    result = result.sort("Account 1")
    expected = pl.DataFrame({
        "Account 1": ["Assets", "Liabilities"],
        "2021": [1200.0, -1200.0],
        "2022": [2400.0, -2400.0],
    })
    assert result.equals(expected)

    result = r.balance_report(df, on="Year", index=["Account 1", "Account 2"])
    result = result.sort(["Account 1", "Account 2"])
    expected = pl.DataFrame({
        "Account 1": ["Assets", "Assets", "Liabilities", "Liabilities"],
        "Account 2": ["Asset 1", "Asset 2", "Liability 1", "Liability 2"],
        "2021": [600.0, 600.0, -600.0, -600.0],
        "2022": [1200.0, 1200.0, -1200.0, -1200.0]
    })
    assert result.equals(expected)


def test_flow_report():
    df = report_df()
    result = r.flow_report(df, on="Year", index="Account 1")
    result = result.sort("Account 1")
    expected = pl.DataFrame({
        "Account 1": ["Assets", "Liabilities"],
        "2021": [1200.0, -1200.0],
        "2022": [1200.0, -1200.0],
    })
    assert result.equals(expected)

    result = r.flow_report(df, on="Year", index=["Account 1", "Account 2"])
    result = result.sort(["Account 1", "Account 2"])
    expected = pl.DataFrame({
        "Account 1": ["Assets", "Assets", "Liabilities", "Liabilities"],
        "Account 2": ["Asset 1", "Asset 2", "Liability 1", "Liability 2"],
        "2021": [600.0, 600.0, -600.0, -600.0],
        "2022": [600.0, 600.0, -600.0, -600.0]
    })
    assert result.equals(expected)


def test_budget_report():
    # Test with no budget txn
    df = report_df()
    result = r.budget_report(df, on="Year", index="Account 1",
                             txn_type_col="Txn type")
    expected = pl.DataFrame({
        "Account 1": ["Assets", "Liabilities"],
        '{2021,"actual"}': [1200.0, -1200.0],
        '{2022,"actual"}': [1200.0, -1200.0],
    })
    assert result.equals(expected)

    # Test with budget txn
    df = report_df(with_budget=True)
    result = r.budget_report(df, on="Year", index="Account 1",
                             txn_type_col="Txn type")
    expected = pl.DataFrame({
        "Account 1": ["Assets", "Liabilities"],
        '{2021,"actual"}': [1200.0, -1200.0],
        '{2021,"budget"}': [1140.0, None],
        '{2022,"actual"}': [1200.0, -1200.0],
        '{2022,"budget"}': [1140.0, None],
    })
    assert result.equals(expected)

    # Test with budget txn cumulative
    df = report_df(with_budget=True)
    result = r.budget_report(df, on="Year", index="Account 1",
                             txn_type_col="Txn type", cumulative=True)
    expected = pl.DataFrame({
        "Account 1": ["Assets", "Liabilities"],
        '{2021,"actual"}': [1200.0, -1200.0],
        '{2021,"budget"}': [1140.0, None],
        '{2022,"actual"}': [2400.0, -2400.0],
        '{2022,"budget"}': [2280.0, None],
    })
    assert result.equals(expected)


def test_write_excel(accounts_file, txns_file, tmp_path):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    df = j.to_polars()
    tmp_file = tmp_path / "test.xlsx"
    df.write_excel(tmp_file)
