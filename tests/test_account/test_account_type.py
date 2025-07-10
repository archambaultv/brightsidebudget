from pydantic_core import ValidationError
import pytest
from brightsidebudget.account.account_type import AccountType

@pytest.mark.parametrize("name", [
    "Actifs", "Passifs", "Capitaux propres", "Revenus", "Dépenses"
])
def test_valid_account_type_names(name):
    acc_type = AccountType(name=name)
    assert acc_type.name == name

@pytest.mark.parametrize("invalid_name", [
    "Assets", "Liabilities", "", "actifs", "Unknown", "Revenu"
])
def test_invalid_account_type_raises(invalid_name):
    with pytest.raises(ValueError):
        AccountType(name=invalid_name)

@pytest.mark.parametrize("name,number", [
    ("Actifs", 1000),
    ("Actifs", 1500),
    ("Actifs", 1999),
    ("Passifs", 2000),
    ("Passifs", 2999),
    ("Capitaux propres", 3000),
    ("Capitaux propres", 3999),
    ("Revenus", 4000),
    ("Revenus", 4999),
    ("Dépenses", 5000),
    ("Dépenses", 5999),
])
def test_validate_number_valid(name, number):
    acc_type = AccountType(name=name)
    acc_type.validate_number(number)  # Should not raise

@pytest.mark.parametrize("name,number", [
    ("Actifs", 999),
    ("Actifs", 2000),
    ("Passifs", 1999),
    ("Passifs", 3000),
    ("Capitaux propres", 2999),
    ("Capitaux propres", 4000),
    ("Revenus", 3999),
    ("Revenus", 5000),
    ("Dépenses", 4999),
    ("Dépenses", 6000)
])
def test_validate_number_invalid(name, number):
    acc_type = AccountType(name=name)
    with pytest.raises(ValueError):
        acc_type.validate_number(number)

def test_lt_comparison():
    a = AccountType(name="Actifs").sort_key()
    b = AccountType(name="Passifs").sort_key()
    c = AccountType(name="Capitaux propres").sort_key()
    d = AccountType(name="Revenus").sort_key()
    e = AccountType(name="Dépenses").sort_key()
    assert a < b < c < d < e

def test_frozen_account_type():
    acc_type = AccountType(name="Actifs")
    with pytest.raises(ValidationError):
        acc_type.name = "New Name" # type: ignore

    with pytest.raises(ValidationError):
        acc_type.name = "Passifs"
