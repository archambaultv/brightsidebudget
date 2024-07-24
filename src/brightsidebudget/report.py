"""
This module contains helper functions to generate reports and manipulate
dataframes.
"""

from datetime import date
from typing import Any, Literal, Union
import polars as pl


def add_year_column(df: pl.DataFrame, col_name: str = "Year") -> pl.DataFrame:
    """
    Add a year column to the dataframe.
    """
    return df.with_columns(
        pl.col("Date").dt.year().cast(pl.Int32).alias(col_name)
        )


def add_month_column(df: pl.DataFrame,
                     col_name: str = "Month",
                     month_type: Literal["number", "short", "long"] = "number"
                     ) -> pl.DataFrame:
    """
    Add a month column to the dataframe.
    """
    if month_type == "number":
        dt = pl.Int32
        expr = pl.col("Date").dt.month()
    elif month_type == "short":
        dt = pl.Utf8
        expr = pl.col("Date").dt.strftime("%b")
    elif month_type == "long":
        dt = pl.Utf8
        expr = pl.col("Date").dt.strftime("%B")
    else:
        raise ValueError(f"Invalid month type {month_type}")
    return df.with_columns(
        expr.cast(dt).alias(col_name)
        )


def add_year_month_column(df: pl.DataFrame, col_name: str = "Year-Month") -> pl.DataFrame:
    """
    Add a year-month (ex: 2024-01) column to the dataframe.
    """
    return df.with_columns(
        pl.col("Date").dt.strftime("%Y-%m").cast(pl.Utf8).alias(col_name)
        )


def add_fiscal_year_column(df: pl.DataFrame,
                           first_fiscal_month: int = 1,
                           col_name: str = "Fiscal Year") -> pl.DataFrame:
    """
    Add a fiscal year column to the dataframe.
    """
    ffm = first_fiscal_month
    return df.with_columns(
        pl.when((ffm == 1) | (pl.col("Date").dt.month() < ffm))
        .then(pl.col("Date").dt.year())
        .otherwise(pl.col("Date").dt.year() + 1)
        .cast(pl.Int32)
        .alias(col_name)
        )


def add_fiscal_month_column(df: pl.DataFrame,
                            first_fiscal_month: int = 1,
                            col_name: str = "Fiscal Month") -> pl.DataFrame:
    """
    Add a fiscal month column to the dataframe.
    """
    return df.with_columns(
        (((pl.col("Date").dt.month() - first_fiscal_month) % 12) + 1)
        .cast(pl.Int32)
        .alias(col_name)
        )


def add_relative_month_column(df: pl.DataFrame,
                              col_name: str = "Relative Month",
                              today: Union[date, None] = None) -> pl.DataFrame:
    """
    Add a relative month column to the dataframe.
    """
    if today is None:
        today = date.today()
    return df.with_columns(
        ((pl.col("Date").dt.year() - today.year) * 12 + pl.col("Date").dt.month() - today.month)
        .cast(pl.Int32)
        .alias(col_name)
        )


def side_by_side(df1: pl.DataFrame,
                 df2: pl.DataFrame,
                 separator: str = "    ") -> str:
    """
    Return a string with the two dataframes side by side.
    """
    df1_str = str(df1)
    df2_str = str(df2)
    df1_lines = df1_str.split("\n")
    df2_lines = df2_str.split("\n")
    max_len = max(len(df1_lines), len(df2_lines))
    lines = []
    for i in range(max_len):
        if i < len(df1_lines):
            line = df1_lines[i]
        else:
            line = " " * len(df1_lines[0])
        if i < len(df2_lines):
            line += separator
            line += df2_lines[i]
        lines.append(line)

    return "\n".join(lines)


def sort_by(df: pl.DataFrame, by: str,
            order_mapping: dict[Any, int],
            maintain_order: bool = False,
            descending: bool = False) -> pl.DataFrame:
    """
    Sort the dataframe by a column based on a mapping of values to order.
    Elements not in the mapping will be sorted last.
    """
    # Create a sort key column
    sort_col = "sort_key"
    while sort_col in df.columns:
        sort_col += "_"

    max_ = max(order_mapping.values()) + 1
    df = (df.with_columns(
                pl.col(by)
                .map_elements(lambda x: order_mapping.get(x, max_), pl.Int32)
                .alias(sort_col))
            .sort(sort_col, descending=descending, maintain_order=maintain_order)
            .drop("sort_key"))

    return df


def balance_report(df: pl.DataFrame,
                   on: Union[str, list[str]] = "Year",
                   index: Union[str, list[str]] = "Account short name",
                   maintain_order: bool = True,
                   sort_columns: bool = True) -> pl.DataFrame:
    """
    Generate a balance report from a dataframe based on the pivot method.

    The columns must exists in the dataframe, except for the default "Year"
    column of `on` parameter which will be added if not present.
    """
    if on == "Year" and "Year" not in df.columns:
        df = add_year_column(df)

    balance_col = "Balance"
    while balance_col in df.columns:
        balance_col += "_"

    if isinstance(index, str):
        index = [index]

    return (
        df.sort(by=index + ["Date"])
        .with_columns(
            pl.col("Amount").cum_sum().over(index).alias(balance_col)
        )
        .pivot(on=on, index=index, values=balance_col, aggregate_function="last",
               maintain_order=maintain_order, sort_columns=sort_columns))


def flow_report(df: pl.DataFrame,
                on: Union[str, list[str]] = "Year",
                index: Union[str, list[str]] = "Account short name",
                maintain_order: bool = True,
                sort_columns: bool = True) -> pl.DataFrame:
    """
    Generate a flow report from a dataframe based on the pivot method.

    The columns must exists in the dataframe, except for the default "Year"
    column of `on` parameter which will be added if not present.
    """
    if on == "Year" and "Year" not in df.columns:
        df = add_year_column(df)

    return df.pivot(on=on, index=index, values="Amount", aggregate_function="sum",
                    maintain_order=maintain_order,
                    sort_columns=sort_columns)


def budget_report(df: pl.DataFrame,
                  on: Union[str, list[str]] = "Year",
                  index: Union[str, list[str]] = "Account short name",
                  txn_type_col: str = "Txn type",
                  cumulative: bool = False,
                  maintain_order: bool = True,
                  sort_columns: bool = True) -> pl.DataFrame:
    """
    Generate a budget report from a dataframe based on the pivot method.

    The columns must exists in the dataframe, except for the default "Year"
    column of `on` parameter which will be added if not present.

    'txn_type_col' is the column that contains the transaction type (ex:
    'actual', 'budget').

    If `cumulative` is True, the balance will be cumulative. Note that in this
    case, if the dataframe contains 'actual' transactions prior to the start of
    the budget period, they will be included in the 'actual' cumulative balance.
    """
    if on == "Year" and "Year" not in df.columns:
        df = add_year_column(df)

    if isinstance(on, str):
        on = [on]
    on = on + [txn_type_col]

    balance_col = "Balance"
    while balance_col in df.columns:
        balance_col += "_"

    if isinstance(index, str):
        index = [index]

    if cumulative:
        agg_func = "last"
        df = (df.sort(by=index + [txn_type_col, "Date"])
                .with_columns(
                    pl.col("Amount").cum_sum().over(index + [txn_type_col]).alias(balance_col)))
    else:
        agg_func = "sum"
        balance_col = "Amount"
    return df.pivot(on=on, index=index, values=balance_col, aggregate_function=agg_func,
                    maintain_order=maintain_order, sort_columns=sort_columns)
