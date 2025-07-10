# Brightside Budget

🎶 Always look on the bright side of your finances 🎶

Brightside Budget is my personal Python library to manage my finances. Expect
this library to be opinionated and tailored to my needs, with frequent changes.

## Overview of the library

The data are stored in an Excel file and the library offers a Journal class. The
Journal class encompasses a collection of accounts, postings, balance
assertions, along with various methods to manipulate these objects.

The command line interface (CLI) allows you to interact with the journal. The
availabe commands are:
- `check`: to check the journal for inconsistencies and errors.
- `import`: to import data into the journal.
- `export`: to export the journal to an another Excel file with additional columns of information.
    This command can also reset the opening balance date of the journal, so you don't have all the prior
    years of data in the exported file.
- `rewrite`: to rewrite the journal while renumbering the transactions and other options.

All of these commands take a configuration file as an argument. See the
[`tests/fixture`](./tests/fixtures/) directory for examples of configuration files.
