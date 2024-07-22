# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html) with
the exception that the versions 0.*.* may have breaking changes in minor versions.

## [0.4.7]
### Fixed
- `from_csv` method of `Journal` now correctly reads empty `short_qname`.

## [0.4.6]
### Added
- Added `short_qname` attribute to `Account` to limit the shortest qualified
  name of an account. This is a breaking change since the `qname` attribute now
  has to be modified with `update_qname` method.

## [0.4.5]
### Fixed
- Fixed `adjust_for_bassertion` when called with a child parameter with a
  shortened qualified name.

## [0.4.4]
### Fixed
- `adjust_for_bassertion` correctly calls `balance` method of `Journal`

## [0.4.3]
### Fixed
- `balance` method of `Journal` now correctly computes the balance of accounts
  with children.

## [0.4.2]
### Changed
- `is_descendant_of` and `is_equal_or_descendant_of` method of `QName` now
  accept a string as argument.

## [0.4.1]
### Changed
- `qname` attribute of `QName` is now called `qstr` (breaking change).

### Fixed
- Fixed default value of optional parameter in `export_for_excel` method of
  `Journal` class to be `None` instead of `[]`.
- Parameter `remove_delimiter_from` of `read_bank_csv` now correctly accepts a string.

## Add
- `acc_qname` attribute or `Posting`, `RPosting`, `BAssertion` can now also be
  set using a simple string. Same for `qname` attribute of `Account`.

## [0.4.0]
### Changed
- Major refactoring of the library. Most classes have changed and the API is not
  backward compatible.
- `Account`, `Posting`, `BAssertion` classes are not MutableMapping anymore.

### Added
- Add `QName` class to handle qualified names and identify accounts.
- Add `Txn` class to group postings together in a transaction.

### Removed
- Removed dependency on `networkx` and `pydantic` libraries.

## [0.3.1] - 2024-06-26
### Fixed
- Fixed a bug in `postings_extra` when computing the fiscal year of a transaction.

## [0.3.0] - 2024-06-05
### Added
- Add a `get_dict` method to MutableMapping classes to get the underlying dictionary.

### Changed
- `Account`, `Posting`, `BAssertion` classes now have writable attributes.

## [0.2.1] - 2024-05-24
### Removed
- Removed `auto_balance` method of `Journal` class as it was not ready for
  production.

## [0.2.0] - 2024-05-24
### Added
- Add a speedtest script to measure the performance of the library.

### Changed
- `Account`, `Posting`, `BAssertion` classes are now `MutableMapping` and by
  default don't recopy the data when creating a new instance from a dictionary.
- Attribute `identifier` of `Account` is now a `name`
- The `postings_extra` is now 50% faster.
- The `journal` class now only computes balances on demand and not all at once
  during initialization.

## [0.1.5] - 2024-05-21
### Fixed
- Fixed a bug in `read_bank_csv` when the amount column was empty instead of 0.


## [0.1.4] - 2024-05-21
### Fixed
- Fixed a bug in `read_bank_csv` when using the `remove_delimiter_from` parameter.


## [0.1.3] - 2024-05-21
### Added
- `read_bank_csv` now accepts a `skiprows` parameter to specify the number of
  rows to skip before reading the CSV file.

### Fixed
- `balance` method of `Account` correctly returns 0 when the journal has no postings.

## [0.1.2] - 2024-05-17
### Added
- `next_txn_id` method of `Journal` to get the next available transaction ID.

### Fixed
- Fixed a bug in `postings_extra` of `Journal` when a custum list of postings
  was provided.

## [0.1.1] - 2024-05-15
### Added
- `from_dict` method of `Account`, `Posting`, `BAssertion` now properly checks
  for the presence of the required keys in the dictionary.
- New `from_dicts` method of `Journal` to create a journal from a list of
  dictionaries.
- More unit tests
### Fixed
- Fixed a bug in the `Journal` class that triggered an `TypeError` when an
  account was not found in the journal's accounts list.
- Journal now checks for that each transaction has one unique date.
- Journal now checks for duplicate balance assertions.

## [0.1.0] - 2024-05-15
Initial release
### Added
- Account, Posting, BAssertion and Journal classes
- Import and deduplication of postings from CSV files
