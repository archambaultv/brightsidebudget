import pytest
from brightsidebudget import QName
from brightsidebudget.account import Account


def test_qname():
    qname = QName("A:B:C")
    assert qname._qstr == "A:B:C"
    assert qname._qlist == ["A", "B", "C"]
    assert qname.depth == 3
    assert qname.parent == QName("A:B")
    assert qname.parent.parent == QName("A")
    assert qname.is_descendant_of(QName("A"))
    assert qname.is_descendant_of(QName("A:B"))
    assert qname.is_descendant_of("A:B")
    assert not qname.is_descendant_of(QName("A:B:C"))
    assert not qname.is_descendant_of(QName("A:B:D"))
    assert not qname.is_descendant_of(QName("A:B:C"))
    assert not qname.is_descendant_of("A:B:C")

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


def test_sort():
    a1 = Account(qname="Actifs:Z")
    a2 = Account(qname="Actifs:A")
    a3 = Account(qname="Capitaux propres:C")
    a4 = Account(qname="Passifs:B")

    ls = [a1, a2, a3, a4]
    assert sorted(ls, key=lambda x: x.qname.sort_key) == [a2, a1, a4, a3]
