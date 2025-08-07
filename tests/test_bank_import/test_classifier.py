from decimal import Decimal
import pytest
import logging
from brightsidebudget.bank_import.bank_csv import BankCsv
from brightsidebudget.bank_import.classifier import RuleClassifier, Rule
from brightsidebudget.account.account import Account
from brightsidebudget.config.import_config import BankCsvConfig

@pytest.fixture
def accounts():
    return {
        "Compte chèque": Account(name="Compte chèque", type="Actifs", number=1001),  # type: ignore
        "Revenus A": Account(name="Revenus A", type="Revenus", number=4001),  # type: ignore
        "Revenus B": Account(name="Revenus B", type="Revenus", number=4002),  # type: ignore
        "Dépenses courantes": Account(name="Dépenses courantes", type="Dépenses", number=5001),  # type: ignore
        "Non classé": Account(name="Non classé", type="Dépenses", number=5999),  # type: ignore
    }

@pytest.fixture
def classifier(accounts, rules_fixture_path):
    logger = logging.getLogger()
    logger.addHandler(logging.NullHandler())
    return RuleClassifier(file=rules_fixture_path, accounts=accounts, 
                          default_account="Non classé", logger=logger)

@pytest.fixture
def account():
    return Account(name="Compte chèque", type="Actifs", number=1001) # type: ignore

@pytest.fixture
def bank_csv(account, bank_csv_fixture_path):
    return BankCsv(
        file=bank_csv_fixture_path,
        account=account,
        config=BankCsvConfig(
        date_col="date",
        stmt_desc_cols=["category", "description"],
        amount_in_col="credit",
        amount_out_col="debit",
        encoding="utf8",
        csv_delimiter=",",
        skiprows=0)
    )

def test_classify(classifier: RuleClassifier, bank_csv: BankCsv):
    # Create a posting that matches the first rule
    ps = bank_csv.get_bank_postings()
    assert len(ps) == 9  # Ensure we have the expected number of postings
    
    txns = []
    for p in ps:
        txn = classifier.classify(posting=p)
        if txn:
            txns.extend(txn)
    assert len(txns) == 8  # One posting discarded (zero amount)

def test_load_rules(classifier: RuleClassifier):
    rules = classifier.load_rules()
    assert len(rules) == 6
    assert isinstance(rules[0], Rule)
    
    # Rule 0: Discard rule for amount equals 0
    rule1 = rules[0]
    assert rule1.account_name is None
    assert rule1.description_equals is None
    assert rule1.amount_equals == Decimal("0")
    assert rule1.amount_less_than is None
    assert rule1.amount_greater_than is None
    assert rule1.second_account_name is None
    assert rule1.discard is True
    
    # Rule 1: ENTREPRISE QUÉBEC INC - positive amounts to Revenus A
    rule2 = rules[1]
    assert rule2.account_name == "Compte chèque"
    assert rule2.description_equals == ["ENTREPRISE QUÉBEC INC"]
    assert rule2.amount_equals is None
    assert rule2.amount_less_than is None
    assert rule2.amount_greater_than == Decimal("0")
    assert rule2.second_account_name == "Revenus A"
    assert rule2.discard is False
    
    # Rule 2: Virement Interac - exact amount 350 to Revenus B
    rule3 = rules[2]
    assert rule3.account_name == "Compte chèque"
    assert rule3.description_equals == ["Virement Interac"]
    assert rule3.amount_equals == Decimal("350")
    assert rule3.amount_less_than is None
    assert rule3.amount_greater_than is None
    assert rule3.second_account_name == "Revenus B"
    assert rule3.discard is False
    
    # Rule 3: METRO PLUS MONTRÉAL to Dépenses courantes
    rule4 = rules[3]
    assert rule4.account_name == "Compte chèque"
    assert rule4.description_equals == ["METRO PLUS MONTRÉAL"]
    assert rule4.amount_equals is None
    assert rule4.amount_less_than is None
    assert rule4.amount_greater_than is None
    assert rule4.second_account_name == "Dépenses courantes"
    assert rule4.discard is False
    
    # Rule 4: Multiple descriptions with negative amounts to Dépenses courantes
    rule5 = rules[4]
    assert rule5.account_name == "Compte chèque"
    assert rule5.description_equals == ["HYDRO-QUÉBEC", "STM OPUS+", "PHARMAPRIX"]
    assert rule5.amount_equals is None
    assert rule5.amount_less_than == Decimal("0")
    assert rule5.amount_greater_than is None
    assert rule5.second_account_name == "Dépenses courantes"
    assert rule5.discard is False
    
    # Rule 5: Default rule - everything else to Non classé
    rule6 = rules[5]
    assert rule6.account_name is None
    assert rule6.description_equals is None
    assert rule6.amount_equals is None
    assert rule6.amount_less_than is None
    assert rule6.amount_greater_than is None
    assert rule6.second_account_name == "Non classé"
    assert rule6.discard is False
