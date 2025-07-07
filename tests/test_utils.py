
from datetime import date
from brightsidebudget.utils import fiscal_year


def test_fiscal_year():
    """
    Calculate the fiscal year for a given date.
    """
    assert fiscal_year(date(2023, 1, 1), first_fiscal_month=1) == 2023
    assert fiscal_year(date(2023, 12, 31), first_fiscal_month=1) == 2023
    assert fiscal_year(date(2023, 1, 1), first_fiscal_month=4) == 2023
    assert fiscal_year(date(2023, 3, 31), first_fiscal_month=4) == 2023
    assert fiscal_year(date(2023, 4, 1), first_fiscal_month=4) == 2024
    assert fiscal_year(date(2023, 12, 31), first_fiscal_month=4) == 2024
    assert fiscal_year(date(2024, 1, 1), first_fiscal_month=4) == 2024
    assert fiscal_year(date(2024, 1, 1), first_fiscal_month=7) == 2024
    assert fiscal_year(date(2024, 6, 30), first_fiscal_month=7) == 2024
    assert fiscal_year(date(2024, 7, 1), first_fiscal_month=7) == 2025
    assert fiscal_year(date(2024, 12, 31), first_fiscal_month=7) == 2025