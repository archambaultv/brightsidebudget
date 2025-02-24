from datetime import date
from decimal import Decimal
import pytest
from brightsidebudget.bsberror import BSBError
from brightsidebudget.posting import Posting
from brightsidebudget.account import Account


def test_posting__init__():
    a = Account(name="Test", number=1001, type="Actifs", group="Groupe", sub_group="Sous-groupe")
    p = Posting(txn_id=1, date=date(2025, 1, 1), account=a, amount=Decimal(100), comment="Comment",
                stmt_date=date(2025, 1, 1), stmt_desc="Desc")
    assert p.txn_id == 1
    assert p.date == date(2025, 1, 1)
    assert p.account == a
    assert p.amount == 100
    assert p.comment == "Comment"
    assert p.stmt_date == date(2025, 1, 1)
    assert p.stmt_desc == "Desc"

    with pytest.raises(BSBError):
        Posting(txn_id=0, date=date(2025, 1, 1), account=a, amount=Decimal(100), comment="Comment",
                stmt_date=date(2025, 1, 1), stmt_desc="Desc")
