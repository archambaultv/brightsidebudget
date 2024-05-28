import pytest
from brightsidebudget import Account


@pytest.mark.parametrize("d",
                         [{"Name": "A", "Parent": "B"},
                          {"Name": "A", "Parent": "B", "number": 1000},
                          {"Name": "A", "Parent": None},
                          {"Name": "A"},
                          {"Name": "A", "desc": "My account A"}])
def test_from_dict(d: dict):
    account = Account.from_dict(d, copy=True)
    assert account.name == d["Name"]
    if "Parent" in d:
        assert account.parent == d["Parent"]
    else:
        d["Parent"] = None
    assert account.get_dict() == d


def test_get_set():
    account = Account(name="A", parent="B")
    assert account.name == "A"
    assert account.parent == "B"
    account.name = "C"
    account.parent = "D"
    assert account.name == "C"
    assert account.parent == "D"
    account["Name"] = "E"
    account["Parent"] = "F"
    assert account.name == "E"
    assert account.parent == "F"

    with pytest.raises(ValueError):
        account.name = ""

    with pytest.raises(ValueError):
        account["Name"] = ""

    with pytest.raises(ValueError):
        account.name = 125

    with pytest.raises(ValueError):
        account["Name"] = ""

    with pytest.raises(ValueError):
        account.parent = 124

    with pytest.raises(ValueError):
        account["Parent"] = 124


@pytest.mark.parametrize("d",
                         [{"Parent": "B"},
                          {},
                          {"Name": ""},
                          {"Name": 125}])
def test_bad_from_dict(d: dict):
    with pytest.raises(ValueError):
        Account.from_dict(d)
