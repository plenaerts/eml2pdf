# eml2pdf

Convert `.eml` (email) files to PDF using Python, making them easier
to archive, share, and view without requiring an email client.

Depends on [GNOME's Pango](https://gitlab.gnome.org/GNOME/pango) and
various Python libraries but NOT on a full rendering engine like
WebKit or Gecko. [python-pdfkit](https://github.com/JazzCore/python-pdf-kit)
and [wkhtmltopdf](https://github.com/wkhtmltopdf/wkhtmltopdf) are
[deprecated libraries](
https://github.com/JazzCore/python-pdfkit?tab=readme-ov-file#deprecation-warning)

Should run on Linux distributions with Pango and Python and macOS. The Pango
dependency is a challenge on Windows at the moment.

This software is in beta state. There are some unit tests, I use it in my own
workflow, but we need some actual users/downloads, basics for translations and
Debian packaging files to proceed to a 1.0 release.

## Features

- Converts email body plain from HTML or plain text message body.
- Tries to filter potential **security or privacy** issues.
- Preserves formatting, character encodings, embedded images.
- Generates a header section with email metadata From, To, Subject, Date and, if
  any, a list of attachments with size and md5sum.

## Dependencies

- Python 3.11+
- [weasyprint](https://weasyprint.org/) - a visual rendering engine for HTML
  and CSS that can export to PDF. Weasyprint depends on [GNOME's Pango](
  https://gitlab.gnome.org/GNOME/pango).
- [python-markdown](https://github.com/Python-Markdown/markdown) - for
  HTML'izing plain text.
- [hurry.filesize](https://pypi.org/project/hurry.filesize/) - return human
  readable filesizes.
- [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) - HTML
  sanitization.

## Installation

On a desktop system, chances are high that you have Pango installed. In this
case you can install eml2pdf from PyPi using pip:

```bash
pip install eml2pdf
```

If weasyprint can't find Pango, best is to [install weasyprint using your
system's package manager](
https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation).

Users of Arch linux or derived distro's like Manjora can use AUR package
[eml2pdf](https://aur.archlinux.org/packages/eml2pdf).

Check [INSTALL.md](INSTALL.md) for more detailed installation instructions if
you need more help.

## Usage

eml2pdf will convert all .eml files in an input directory and
save converted PDF files in a specified output directory.

The output filenames are formatted as:
`YYYY-MM-DD_subject[-counter].pdf`, where:

- The date prefix is taken from the email's sent date.
- The email subject is taken from the email headers.
- Should there be any duplicate filenames, then a counter will be added.
- The extension is changed to `.pdf`

For example, `some_file.eml` with subject "My Email" sent on March 15, 2024
will become `2024-03-15_My_Email.pdf`.

```text
usage: eml2pdf [-h] [-d] [-n number] [-p size] [-v] input_dir output_dir

Convert EML files to PDF

positional arguments:
  input_dir             Directory containing EML files
  output_dir            Directory for PDF output

options:
  -h, --help            Show this help message and exit.
  -d, --debug_html      Write intermediate html file next to pdf's.
  -n number, --number-of-procs number
                        Number of parallel processes. Defaults to the number
                        of available logical CPU's to eml2pdf.
  -p size, --page size  a3 a4 a5 b4 b5 letter legal or ledger with or without
                        'landscape', for example: 'a4 landscape' or 'a3'
                        including quotes. Defaults to 'a4', implying portrait.
  --unsafe              Don't sanitize HTML from potentially unsafe elements
                        such as remote images, scripts, etc. This may expose
                        sensitive user information.
  -v, --verbose         Show a lot of verbose debugging info. Forces number
                        of procs to 1.
```

Example below renders all .eml files in `./emails` to a4 landscape oriented pdf's
in `./pdf`:

```bash
eml2pdf -p 'a4 landscape' ./emails ./pdfs
```

### Debug HTML

eml2pdf will first parse email header info such as date, subject, etc. Next
the mail body will be parsed. If there is an HTML body, eml2pdf will clean
this HTML body (ref. below under Security) and prepend this resulting HTML with
a summary table.

In a next step this HTML is rendered by weasyprint to a PDF.

The '--debug_html' flag will save this intermediate HTML. You can use this to
check if there is an email parsing issue in eml2pdf or a PDF conversion issue
in weasyprint.

### Page size

Not all emails are properly formatted. Part of your mail might not be visible
in the pdf in case an email doesn't limit width of some elements such as
images, tables or others. You can play with page sizes and orientations to try
and accomodate wide emails.

### Security

#### HTML Sanitization

Emails can contain HTML which can contain stuff you don't expect or want.

In the best case your emails contain clean HTML.

In common cases they will contain intentional tracking of end users using
forged remote sources for images and other resources. This is a common
practice in marketing or mass mailing solutions.

eml2pdf tries to keep the formatting in your mails ánd clean up
potentially malicious content using custom filtering of tags, remote images,
remote stylesheets, etc.

We try to cleanup. We can't give you a 100% guarantee. If you're very worried,
please cleanup your mails yourself.

You can use the --unsafe flag if you don't want eml2pdf to try and
sanitize your mails. Check your mails' content before you use this flag!

#### MD5 sums of attachments

eml2pdf lists attachments with their md5sums. You can use these md5sums for
your convenience. They give a very strong indication that files are not
altered. **They will not be usable as proof in courts of law.**
They are not intended to be.

## Reporting issues

We've tested eml2pdf with a couple of cases with embedded images, tables,
unicode or specific encodings. Refer to [tests](tree/main/tests) for example
emails.

Please open an issue ticket if you have a mail where conversion results are
not usable. Describe what you think your message contains and the output you
expect. Attach verbose eml2pdf output of only this eml file and attach
the eml file itself. We're not promising a solution, but we can
have a look.

**Please cleanup any attachments you add. Remove things you don't want to share with
the world.**

## Credits

eml2pdf was originally forked from [klokie/eml-to-pdf](
https://github.com/klokie/eml-to-pdf) by [Daniel Grossfeld](
https://github.com/klokie/).

## License

eml2pdf code is published under the MIT license.

Licenses for dependencies:

- weasyprint: BSD-3
- python-markdown: BSD-3
- hurry.filesize: ZPL 2.1
- beautifulsoup4: MIT
- Pango: GPLv2
