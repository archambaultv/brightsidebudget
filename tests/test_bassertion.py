from datetime import date
from decimal import Decimal
from brightsidebudget.account import Account
from brightsidebudget.bassertion import BAssertion


def test_bassertion__init__():
    a = Account(name="Test", number=1001, type="Actifs", group="Groupe", sub_group="Sous-groupe")
    b = BAssertion(account=a, date=date(2025, 1, 1), balance=Decimal(100), comment="Comment")
    assert b.account == a
    assert b.date == date(2025, 1, 1)
    assert b.balance == 100
    assert b.comment == "Comment"
