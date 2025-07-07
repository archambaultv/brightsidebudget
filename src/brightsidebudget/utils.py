from datetime import date as date_type

def fiscal_year(date: date_type, first_fiscal_month: int = 1) -> int:
    """
    Calculate the fiscal year for a given date.
    """
    if first_fiscal_month == 1 or date.month < first_fiscal_month:
        return date.year
    else:
        return date.year + 1