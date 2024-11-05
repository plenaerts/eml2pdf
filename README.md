# eml-to-pdf

Convert `.eml` (email) files to PDF using Python.

The converted PDF files will be saved in the same location as the input files with the same name but `.pdf` extension.

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
- `fpdf2` - PDF generation
- `beautifulsoup4` - HTML parsing
- `chardet` - Character encoding detection

Install dependencies using:

```
pip install -r requirements.txt
```

## Usage

```
python eml-to-pdf.py <input_dir> <output_dir>
```

## License

MIT
