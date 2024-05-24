# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html) with
the exception that the versions 0.*.* may have breaking changes in minor versions.

## Unreleased
### Added
- Add a speedtest script to measure the performance of the library.

### Changed
- `Account`, `Posting`, `BAssertion` classes are now `MutableMapping` and by
  default don't recopy the data when creating a new instance from a dictionary.
- Attribute `identifier` of `Account` is now a `Name`

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
