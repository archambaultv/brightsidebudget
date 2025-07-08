# Brightside Budget

🎶 Always look on the bright side of your finances 🎶

Brightside Budget is my personal Python library to manage my finances. Expect
this library to be opinionated and tailored to my needs, with frequent changes.

## Overview of the library

The data are stored in an Excel file and the library offers a Journal class. The
Journal class encompasses a collection of accounts, postings, balance
assertions, along with various methods to manipulate these objects.

The command line interface (CLI) allows you to interact with the journal. The
two commands available are:
- `check`: to check the journal for inconsistencies and errors.
- `import`: to import data into the journal.

Both of these commands take a configuration file as an argument. See the
`tests/fixture` directory for examples of configuration files.
