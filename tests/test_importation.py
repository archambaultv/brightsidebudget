from brightsidebudget import Journal, read_bank_csv, remove_duplicates, balance_posting, \
    Posting


def test_read_bank_csv(bank_checking_file):
    ps = read_bank_csv(bank_checking_file, "Checking", date_col="Date",
                       amount_in_col="Credit", amount_out_col="Debit")
    assert len(ps) == 5


def test_remove_delemiter_from(bank_checking_err_delimiter):
    #  Date,Description,Category,Debit,Credit,Balance
    ps = read_bank_csv(bank_checking_err_delimiter, "Checking", date_col="Date",
                       remove_delimiter_from="Internet, transfert",
                       amount_in_col="Credit", amount_out_col="Debit")
    assert len(ps) == 5


def test_remove_duplicates(bank_checking_file, accounts_file, txns_file):
    j = Journal.from_csv(accounts=accounts_file, postings=txns_file)
    ps = read_bank_csv(bank_checking_file, "Checking", date_col="Date",
                       amount_in_col="Credit", amount_out_col="Debit")
    assert len(ps) == 5
    ps = remove_duplicates(ps, j, fingerprint_tags=["Description"])
    assert len(ps) == 4


def test_balance_posting(bank_checking_file):
    ps = read_bank_csv(bank_checking_file, "Checking", date_col="Date",
                       amount_in_col="Credit", amount_out_col="Debit")

    def foo(p: Posting):
        if p.tags["Description"] == "Super market":
            return [("Food", -p.amount)]
        else:
            return [("Other expenses", -p.amount)]

    ps2 = balance_posting(ps, foo)
    assert len(ps2) == 5
