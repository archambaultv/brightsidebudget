# Brightside Budget
🎶 Always look on the bright side of your finance 🎶

Brightside budget is my personal python library to manage my finance.

## Overview of the library
The data is stored in CSV files, and the library offers a Journal class. The
Journal class encompasses a collection of accounts, postings, balance assertions
and budget targets, along with various methods to manipulate these objects.
Additionally, the library provides essential functionalities for importing,
exporting and deduplicating data.

I use CSV files because they are straightforward to work with in Excel and are
easy to version control with Git. 

My workflow includes:

- Importing bank transactions into the journal
- Exporting the journal postings with added metadata to a CSV file 
- Linking the CSV file in Excel for analysis