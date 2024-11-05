# eml-to-pdf

Convert `.eml` (email) files to PDF using Python.

The converted PDF files will be saved in the specified output directory. The output filenames are formatted as:
`YYYY-MM-DD_original_filename.pdf`, where:

- The date prefix is taken from the email's sent date
- Spaces in the original filename are converted to underscores
- The extension is changed to `.pdf`

For example, `My Email.eml` sent on March 15, 2024 will become `2024-03-15_My_Email.pdf`.

## Features

- Converts email body (both plain text and HTML)
- Preserves email metadata (From, To, Subject, Date)
- Handles email attachments (listed in the PDF)
- Supports various character encodings
- Maintains basic text formatting

## Purpose

This tool allows you to convert email files (`.eml` format) into PDF documents, making them easier to archive, share, and view without requiring an email client.

## Dependencies

- Python 3.6+
- `email` (built-in Python library)
- `pdfkit` - HTML to PDF conversion

Install dependencies using:

```
pip install -r requirements.txt
```

## Usage

```
python eml-to-pdf.py <input_dir> <output_dir>
```

For example:

```
python eml-to-pdf.py ./emails ./pdfs
```

Input file: `Meeting Notes.eml` (sent 2024-03-20)
Output file: `2024-03-20_Meeting_Notes.pdf`

## License

MIT
