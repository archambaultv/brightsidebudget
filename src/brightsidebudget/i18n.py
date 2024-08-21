class AccountHeader():
    def __init__(self, *, account: str = "Account"):
        self.account = account

    def __iter__(self):
        return iter([self.account])


class TxnHeader():
    def __init__(self, *, txn: str = "Txn", date: str = "Date", account: str = "Account",
                 amount: str = "Amount", comment: str = "Comment",
                 stmt_desc: str = "Statement description", stmt_date: str = "Statement date"):
        self.txn = txn
        self.date = date
        self.account = account
        self.amount = amount
        self.comment = comment
        self.stmt_desc = stmt_desc
        self.stmt_date = stmt_date

    def __iter__(self):
        return iter([self.txn, self.date, self.account, self.amount, self.comment, self.stmt_desc,
                     self.stmt_date])


class BAssertionHeader():
    def __init__(self, *, date: str = "Date", account: str = "Account", balance: str = "Balance"):
        self.date = date
        self.account = account
        self.balance = balance

    def __iter__(self):
        return iter([self.date, self.account, self.balance])


class TargetHeader():
    def __init__(self, *, start_date: str = "Start date", account: str = "Account",
                 amount: str = "Amount",
                 comment: str = "Comment", frequency: str = "Frequency", interval: str = "Interval",
                 count: str = "Count", until: str = "Until"):
        self.start_date = start_date
        self.account = account
        self.amount = amount
        self.comment = comment
        self.frequency = frequency
        self.interval = interval
        self.count = count
        self.until = until

    def __iter__(self):
        return iter([self.start_date, self.account, self.amount, self.comment, self.frequency,
                     self.interval, self.count, self.until])


class DataframeHeader():
    def __init__(self, *, txn: str = "Txn", date: str = "Date", account: str = "Account",
                 account_short: str = "Account short name", amount: str = "Amount",
                 comment: str = "Comment", stmt_date: str = "Stmt date",
                 stmt_desc: str = "Stmt description"):
        self.txn = txn
        self.date = date
        self.account = account
        self.account_short = account_short
        self.amount = amount
        self.comment = comment
        self.stmt_date = stmt_date
        self.stmt_desc = stmt_desc

    def __iter__(self):
        return iter([self.txn, self.date, self.account, self.account_short, self.amount,
                     self.comment,
                     self.stmt_date, self.stmt_desc])
