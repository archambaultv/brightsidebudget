# Brightside Budget
🎶 Always look on the bright side of your finance 🎶

Brightside budget is my personal python library to manage my finance.

## Overview of the library
The data is stored in CVS files and the library provides a `Journal` class. The
`Journal` class is a collection of `Account`, `Posting` and `BAssertion` objects
and various methods to manipulate them. CSV files are both easy to work with in
Excel and also easy to version control with git. The library also provides basic
functionalities to import and deduplicate.

My workflow is:
- import my bank transactions to my journal
- export the journal postings with added metadata to a CSV file
- link the CSV file in Excel with power query. All analysis is done in Excel.