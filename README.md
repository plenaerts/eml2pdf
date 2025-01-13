# eml_to_pdf

Convert `.eml` (email) files to PDF using only Python.

The converted PDF files will be saved in the specified output directory.
The output filenames are formatted as:
`YYYY-MM-DD_subject[-counter].pdf`, where:

- The date prefix is taken from the email's sent date.
- The email subject is taken from the email headers.
- Should there be any duplicate filenames, then a counter will be added.
- The extension is changed to `.pdf`

For example, `some_file.eml` with subject "My Email" sent on March 15, 2024
will become `2024-03-15_My_Email.pdf`.

## Features

- Converts email body (plain text if there is no HTML body)
- Preserves formatting, character encodings, embedded images.
- Preserves email metadata (From, To, Subject, Date)
- Lists attachments.

## Purpose

This tool allows you to convert email files (`.eml` format) into PDF documents,
making them easier to archive, share, and view without requiring an email
client.

Based on various libraries but NOT on a full rendering engine like WebKit
or Gecko. [python-pdfkit and wkhtmltopdf are deprecated libraries](
    https://github.com/JazzCore/python-pdfkit?tab=readme-ov-file#deprecation-warning)

## Dependencies

- Python 3.11+
- [weasyprint](https://weasyprint.org/) - a visual rendering engine for HTML
and CSS that can export to PDF.
- [python-markdown](https://github.com/Python-Markdown/markdown) - for
  HTML'izing plain text.
- [hurry.filesize](https://pypi.org/project/hurry.filesize/) - return human
  readable filesizes.

## Installation

Clone or download this repo and use pip to install this package:

```bash
pip install .
```

Users of Arch linux or derived distro's like Manjora can use AUR package
[eml_to_pdf](https://aur.archlinux.org/packages/eml_to_pdf-git).

## Usage

```text
usage: eml_to_pdf.py [-h] [-d] [-n number] [-p size] [-v] input_dir output_dir

Convert EML files to PDF

positional arguments:
  input_dir             Directory containing EML files
  output_dir            Directory for PDF output

options:
  -h, --help            Show this help message and exit.
  -d, --debug_html      Write intermediate html file next to pdf's.
  -n number, --number-of-procs number
                        Number of parallel processes. Defaults to the number
                        of available logical CPU's to eml_to_pdf.
  -p size, --page size  a3 a4 a5 b4 b5 letter legal or ledger with or without
                        'landscape', for example: 'a4 landscape' or 'a3'
                        including quotes. Defaults to 'a4'. And 'landscape'.
  -v, --verbose         Show a lot of verbose debugging info. Forces number
                        of procs to 1.
```

Example below renders all .eml files in `./emails` to a4 landscape oriented pdf's
in `./pdf`:

```bash
python eml-to-pdf.py -p 'a4 landscape' ./emails ./pdfs
```

Input file: `Meeting Notes.eml` (sent 2024-03-20)
Output file: `2024-03-20_Meeting_Notes.pdf`

## Issues

We've tested eml_to_pdf with a couple of cases with embedded images, tables,
unicode or specific encodings. Refer to
[tests](/klokie/eml-to-pdf/tree/main/tests) for example emails.

Please open an issue ticket if you have a mail where conversion results are
not usable. Describe what you think your message contains and the output you
expect. Attach verbose eml_to_pdf output of only this eml file and attach
the eml file itself. We're not promising a solution, but we can
have a look.

**Please cleanup any attachments you add of things you don't want to share with
the world.**

## License

eml_to_pdf code is published under the MIT license.

Licenses for dependencies:

- weasyprint: BSD-3
- python-markdown: BSD-3
- hurry.filesize: ZPL 2.1
