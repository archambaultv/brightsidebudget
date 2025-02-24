import pytest
from brightsidebudget.bsberror import BSBError
from brightsidebudget.account import Account


def test_account__init__():
    a = Account(name="Test", number=1001, type="Actifs", group="Groupe", sub_group="Sous-groupe")
    assert a.name == "Test"
    assert a.number == 1001
    assert a.type == "Actifs"
    assert a.group == "Groupe"
    assert a.sub_group == "Sous-groupe"

    with pytest.raises(ValueError):
        Account(name="", number=1001, type="Actifs", group="Groupe", sub_group="Sous-groupe")
    with pytest.raises(BSBError):
        Account(name="Test", number=1001, type="", group="Groupe", sub_group="Sous-groupe")
    with pytest.raises(BSBError):
        Account(name="Test", number=1, type="Actifs", group="Groupe", sub_group="Sous-groupe")
    with pytest.raises(BSBError):
        Account(name="Test", number=1001, type="Toto", group="Groupe", sub_group="Sous-groupe")
