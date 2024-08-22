"""
This module contains helper functions to manipulate dataframes.
"""

from datetime import date
from typing import Literal, Union
import polars as pl


def add_year_column(df: pl.DataFrame, col_name: str = "Year",
                    date_col: str = "Date") -> pl.DataFrame:
    """
    Add a year column to the dataframe.
    """
    return df.with_columns(
        pl.col(date_col).dt.year().cast(pl.Int32).alias(col_name)
        )


def add_month_column(df: pl.DataFrame,
                     col_name: str = "Month",
                     month_type: Literal["number", "short", "long"] = "number",
                     date_col: str = "Date"
                     ) -> pl.DataFrame:
    """
    Add a month column to the dataframe.
    """
    if month_type == "number":
        dt = pl.Int32
        expr = pl.col(date_col).dt.month()
    elif month_type == "short":
        dt = pl.Utf8
        expr = pl.col(date_col).dt.strftime("%b")
    elif month_type == "long":
        dt = pl.Utf8
        expr = pl.col(date_col).dt.strftime("%B")
    else:
        raise ValueError(f"Invalid month type {month_type}")
    return df.with_columns(
        expr.cast(dt).alias(col_name)
        )


def add_year_month_column(df: pl.DataFrame, col_name: str = "Year-Month",
                          date_col: str = "Date") -> pl.DataFrame:
    """
    Add a year-month (ex: 2024-01) column to the dataframe.
    """
    return df.with_columns(
        pl.col(date_col).dt.strftime("%Y-%m").cast(pl.Utf8).alias(col_name)
        )


def add_fiscal_year_column(df: pl.DataFrame,
                           first_fiscal_month: int = 1,
                           col_name: str = "Fiscal Year",
                           date_col: str = "Date") -> pl.DataFrame:
    """
    Add a fiscal year column to the dataframe.
    """
    ffm = first_fiscal_month
    return df.with_columns(
        pl.when((ffm == 1) | (pl.col(date_col).dt.month() < ffm))
        .then(pl.col(date_col).dt.year())
        .otherwise(pl.col(date_col).dt.year() + 1)
        .cast(pl.Int32)
        .alias(col_name)
        )


def add_fiscal_month_column(df: pl.DataFrame,
                            first_fiscal_month: int = 1,
                            col_name: str = "Fiscal Month",
                            date_col: str = "Date") -> pl.DataFrame:
    """
    Add a fiscal month column to the dataframe.
    """
    return df.with_columns(
        (((pl.col(date_col).dt.month() - first_fiscal_month) % 12) + 1)
        .cast(pl.Int32)
        .alias(col_name)
        )


def add_relative_month_column(df: pl.DataFrame,
                              col_name: str = "Relative Month",
                              today: Union[date, None] = None,
                              date_col: str = "Date") -> pl.DataFrame:
    """
    Add a relative month column to the dataframe.
    """
    if today is None:
        today = date.today()
    return df.with_columns(
        ((pl.col(date_col).dt.year() - today.year) * 12 + pl.col(date_col).dt.month() - today.month)
        .cast(pl.Int32)
        .alias(col_name)
        )


def add_txn_accounts_column(df: pl.DataFrame,
                            col_name: str = "Txn Accounts",
                            txn_col: str = "Txn",
                            acc_name: str = "Account short name",
                            delimiter: str = " | ") -> pl.DataFrame:
    """
    Add a column with the accounts involved in the transaction.
    """
    grouped_df = df.group_by(txn_col).agg(
        pl.col(acc_name).unique().sort().str.concat(delimiter=delimiter).alias(col_name)
    )
    return df.join(grouped_df, on=txn_col, how="left")
