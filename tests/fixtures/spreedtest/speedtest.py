import timeit
from brightsidebudget.journal import Journal


def main():
    j = Journal.from_csv('tests/fixtures/spreedtest/accounts.csv',
                         'tests/fixtures/spreedtest/txns.csv',
                         'tests/fixtures/spreedtest/bassertions.csv')
    j.check_bassertions()
    today = j.postings[-1].date
    j.postings_extra(today=today)


if __name__ == '__main__':
    # Time the main function
    t = timeit.timeit(main, number=1)
    print(f"Time: {t:.2f} seconds")
