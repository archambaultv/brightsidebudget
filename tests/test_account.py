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
    assert account.name() == d["Name"]
    if "Parent" in d:
        assert account.parent() == d["Parent"]
    else:
        d["Parent"] = None
    assert account.get_dict() == d


@pytest.mark.parametrize("d",
                         [{"Parent": "B"},
                          {},
                          {"Name": ""},
                          {"Name": 125}])
def test_bad_from_dict(d: dict):
    with pytest.raises(ValueError):
        Account.from_dict(d)
