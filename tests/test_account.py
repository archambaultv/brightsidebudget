import pytest
from pydantic import ValidationError
from brightsidebudget import Account


@pytest.mark.parametrize("d",
                         [{"Account": "A", "Parent": "B"},
                          {"Account": "A", "Parent": "B", "number": 1000},
                          {"Account": "A", "Parent": None},
                          {"Account": "A"},
                          {"Account": "A", "desc": "My account A"}])
def test_from_dict(d: dict):
    account = Account.from_dict(d)
    assert account.identifier == d["Account"]
    if "Parent" in d:
        assert account.parent == d["Parent"]
    for k, v in d.items():
        if k not in ["Account", "Parent"]:
            assert account.tags[k] == v


@pytest.mark.parametrize("d",
                         [{"Parent": "B"},
                          {},
                          {"Account": ""},
                          {"Account": 125}])
def test_bad_from_dict(d: dict):
    with pytest.raises((ValidationError, ValueError)):
        Account.from_dict(d)
