from brightsidebudget import Journal, import_bank_csv, BankCsv
from brightsidebudget.posting import Posting, Txn


def classifier(p: Posting) -> Txn:
    p2 = p.copy()
    p2.amount = -p.amount
    if p.stmt_desc == "Super market":
        p2.acc_qname = "Food"
        return Txn([p, p2])
    else:
        p2.acc_qname = "Expenses:Other"
        return Txn([p, p2])


def test_read_bank_csv(bank_checking_file, accounts_file, txns_file):
    bank = BankCsv(file=bank_checking_file, qname="Checking", date_col="Date",
                   amount_in_col="Credit", amount_out_col="Debit",
                   stmt_desc_cols=["Description"])
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    txns = import_bank_csv(j, bank, classifier)
    assert len(txns) == 4
    assert txns[0].postings[0].acc_qname.qstr == "Assets:Checking"
    assert txns[0].postings[1].acc_qname.qstr == "Expenses:Food"


def test_remove_delemiter_from(bank_checking_bad_delimiter, accounts_file, txns_file):
    bank = BankCsv(file=bank_checking_bad_delimiter, qname="Checking", date_col="Date",
                   amount_in_col="Credit", amount_out_col="Debit",
                   remove_delimiter_from="An unquoted, comma",
                   stmt_desc_cols=["Description"])
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    txns = import_bank_csv(j, bank, classifier)
    assert len(txns) == 4
