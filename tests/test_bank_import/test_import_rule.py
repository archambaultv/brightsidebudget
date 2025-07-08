import pytest
from brightsidebudget.bank_import.import_rule import Rule


def test_wrong_dict_keys():
    d = {
        "account_name": "Compte chèque",
        "description_equals": ["Hypothèque"],
        "amount": -782.93,  # amount should be amount_equals
        "second_account_name": "Hypothèque"}

    with pytest.raises(ValueError):
        Rule(**d)