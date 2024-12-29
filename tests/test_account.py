import pytest
from brightsidebudget import QName
from brightsidebudget.account import Account


def test_qname():
    qname = QName("A:B:C")
    assert qname.qstr == "A:B:C"
    assert qname.qlist == ["A", "B", "C"]
    assert qname.depth == 3
    assert qname.parent == QName("A:B")
    assert qname.parent.parent == QName("A")
    assert qname.is_descendant_of(QName("A"))
    assert qname.is_descendant_of(QName("A:B"))
    assert qname.is_descendant_of("A:B")
    assert not qname.is_descendant_of(QName("A:B:C"))
    assert not qname.is_descendant_of(QName("A:B:D"))
    assert qname.is_equal_or_descendant_of(QName("A:B:C"))
    assert qname.is_equal_or_descendant_of("A:B:C")

    assert QName("A").depth == 1
    assert QName("A").parent is None

    assert QName("A:B:C") == QName(["A", "B", "C"])

    assert QName("A") < QName("B")
    assert QName("A") < QName("A:B")
    assert QName("A:B") < QName("A:C")
    assert QName("A:B") < QName("AA:B")
    assert QName("A:B") < QName("A!:B")
    assert QName("AAA:B:C") < QName("B")

    for bad in ["A:", ":A", ":", "A::C", ""]:
        with pytest.raises(ValueError):
            QName(bad)

        bad_list = bad.split(":")
        with pytest.raises(ValueError):
            QName(bad_list)

    with pytest.raises(ValueError):
        QName([])

    with pytest.raises(ValueError):
        QName(["A:B"])


def test_account():
    acc = Account(qname="A:B:C")
    assert acc.qname == QName("A:B:C")

    acc2 = acc.copy()
    assert acc2.qname == QName("A:B:C")

    # Change name
    acc.qname = "D:E:F"
    assert acc.qname == QName("D:E:F")
