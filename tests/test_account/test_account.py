import pytest
from brightsidebudget.account.account import Account
from brightsidebudget.account.account_type import AccountType


def test_account_init_valid():
    atype = AccountType(name="Actifs")
    acc = Account(name="Caisse", type=atype, number=1001, group="Courant", subgroup="Petite caisse")
    assert acc.name == "Caisse"
    assert acc.type == atype
    assert acc.group == "Courant"
    assert acc.subgroup == "Petite caisse"
    assert acc.number == 1001

def test_account_init_empty_name():
    atype = AccountType(name="Actifs")
    with pytest.raises(ValueError):
        Account(name="", type=atype, number=1001)

def test_account_init_invalid_number():
    atype = AccountType(name="Actifs")
    with pytest.raises(ValueError):
        Account(name="Caisse", type=atype, number=-1)

def test_account_type_str():
    acc = Account(name="Crédit", type="Passifs", number=2001) # type: ignore
    assert acc.type == AccountType(name="Passifs")