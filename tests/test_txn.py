from datetime import date
from decimal import Decimal
import pytest
from brightsidebudget.bsberror import BSBError
from brightsidebudget.posting import Posting
from brightsidebudget.account import Account
from brightsidebudget.txn import Txn


def test_posting__init__():
    a1 = Account(name="Test", number=1001, type="Actifs", group="Groupe", sub_group="Sous-groupe")
    p1 = Posting(txn_id=1, date=date(2025, 1, 1), account=a1, amount=Decimal(100),
                 comment="Comment", stmt_date=date(2025, 1, 1), stmt_desc="Desc")

    a2 = Account(name="Test2", number=1002, type="Actifs", group="Groupe", sub_group="Sous-groupe")
    p2 = Posting(txn_id=1, date=date(2025, 1, 1), account=a2, amount=Decimal(-100),
                 comment="Comment2", stmt_date=date(2025, 1, 1), stmt_desc="Desc2")

    t = Txn(postings=[p1, p2])
    assert len(t) == 2
    assert t.is_1_n() is True
    assert t.has_zero_amount() is False
    assert t.is_uncategorized() is False
    assert t.txn_id == 1
    assert t.date == date(2025, 1, 1)
    assert t.accounts() == [a1, a2]

    with pytest.raises(ValueError):
        Txn(postings=[])

    with pytest.raises(ValueError):
        p = p2.copy()
        p.txn_id = 2
        Txn(postings=[p1, p])

    with pytest.raises(BSBError):
        Txn(postings=[p1, p1])

    with pytest.raises(BSBError):
        p = p2.copy()
        p.date = date(2025, 1, 2)
        Txn(postings=[p1, p])
