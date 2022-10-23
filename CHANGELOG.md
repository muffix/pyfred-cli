# Changelog

## UNRELEASED

- Added an optional `--upgrade` flag to the `vendor` command which will be passed through to the `pip install` command
  if set.

## v0.1.4 - 2022-10-23

- Fixes a bug where not all files were included in the template

## v0.1.3 - 2022-10-21

- Updates the workflow template to import dependencies from the `vendored` module

## v0.1.2 - 2022-10-17

- Searches for the workflows location in either the configured sync directory or the default location

## v0.1.1 - 2022-10-16

- Added a `--debug` flag to the CLI

## v0.1.0 - 2022-10-16

- Initial release
