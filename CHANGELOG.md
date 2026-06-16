# Eml2pdf changelog

## v2.1.0 - Unreleased

- Support in-memory EML to PDF conversion - contributed by [Levi Lesches](https://github.com/Levi-Lesches)
- Added loglevel tests and fixes

## v2.0.2 - 2026-04-10

- Bugfix - Header class renamed to internal - contributed by
  [benhxy](https://github.com/benhxy)
- Added tests that would have prevented above.

## v2.0.1 - 2026-04-09

- Fix errors in README.md

## v2.0 - 2026-04-09

<!-- pyml disable-next-line no-emphasis-as-heading-->
**Breaking changes to the CLI and API**

- `eml2pdf` command line script now supports:
  1) converting all eml files in a directory to pdf using subcommand
  `convert_dir` and
  2) converting a single eml file to a pdf file using subcommand
  `convert_file`. Idea contributed by
  [bastidest](https://github.com/bastidest).
- The API is cleaned up, functions starting with a _ are "internal".
  Feel free to use `eml2pdf.libeml2pdf:process_eml` and others 👍
- Fix CTE 8bit with UTF-8 encoding - contributed by
  [bastidest](https://github.com/bastidest).
- Improved logging feedback:
  - Added `--quiet` command line argument.
  - Tuned down too chatty logging from weasyprint and fonttools.

## v1.1 - 2025-12-25

- Inline attachments that are not images - contributed by
  [omusale](https://github.com/omusale)
- Project tasks using poe
- Documentation

## v1.0 - 2025-11-25

- Fix issue #1 - support cpu count on Windows.
- Split off libeml2pdf from eml2pdf module to prepare for GUI support.
- README.md: AUR package renamed.

## v0.1.1 - 2025-02-09

- Fix broken 'pip install' when downloading source archive from github.
