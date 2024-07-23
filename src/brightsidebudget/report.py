"""
This module contains helper functions to generate reports and manipulate
dataframes.
"""

from typing import Literal, Union
import polars as pl


def add_year_column(df: pl.DataFrame, col_name: str = "Year") -> pl.DataFrame:
    """
    Add a year column to the dataframe.
    """
    return df.with_columns(
        pl.col("Date").dt.year().alias(col_name)
        )


def add_month_column(df: pl.DataFrame,
                     col_name: str = "Month",
                     month_type: Literal["number", "short", "long"] = "number"
                     ) -> pl.DataFrame:
    """
    Add a month column to the dataframe.
    """
    if month_type == "number":
        expr = pl.col("Date").dt.month()
    elif month_type == "short":
        expr = pl.col("Date").dt.strftime("%b")
    elif month_type == "long":
        expr = pl.col("Date").dt.strftime("%B")
    else:
        raise ValueError(f"Invalid month type {month_type}")
    return df.with_columns(
        expr.alias(col_name)
        )


def add_year_month_column(df: pl.DataFrame, col_name: str = "Year-Month") -> pl.DataFrame:
    """
    Add a year-month (ex: 2024-01) column to the dataframe.
    """
    return df.with_columns(
        pl.col("Date").dt.strftime("%Y-%m").alias(col_name)
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
        .alias(col_name)
        )


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
