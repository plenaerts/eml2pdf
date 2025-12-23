# EML Parsing and Processing Flow

## Overview

This document describes how eml2pdf parses EML (email) files and processes their various parts to generate PDF documents. The main processing logic is implemented in `eml2pdf/libeml2pdf.py`.

## High-Level Processing Flow

```
EML File
    ↓
Parse with email.message module (libeml2pdf.py:352-353)
    ↓
Extract Header (libeml2pdf.py:355)
    ↓
Walk Message Parts (libeml2pdf.py:356)
    ↓
Generate Attachment List (libeml2pdf.py:357)
    ↓
Combine into HTML (libeml2pdf.py:363-370)
    ↓
Sanitize HTML (if not --unsafe)
    ↓
Generate PDF (libeml2pdf.py:375-376)
```

## Core Components

### 1. Email Class (libeml2pdf.py:35-39)

The `Email` class encapsulates a parsed email:

```python
class Email:
    def __init__(self, msg: email.message.Message, eml_path: Path):
        self.header = Header(msg, eml_path)
        self.html, self.attachments = walk_eml(msg, eml_path)
```

### 2. Header Class (libeml2pdf.py:42-79)

The `Header` class extracts and formats email metadata:

**Extracted Fields**:
- `from_addr` - Sender address
- `to_addr` - Recipient address
- `subject` - Email subject
- `date` - Parsed datetime object
- `formatted_date` - Human-readable date string
- `html` - HTML table representation of header

**Decoding Strategy**:
Headers are decoded using `header_to_html()` (libeml2pdf.py:82-101):
1. Uses `email.header.decode_header()` to parse encoded headers
2. Handles multi-part headers by concatenating them
3. For string parts, uses them directly
4. For byte parts, decodes with specified encoding (defaults to 'ascii' if None)
5. HTML-escapes the result to prevent XSS

**Error Handling**:
- UnicodeError during header decoding is caught and logged (libeml2pdf.py:59-61)
- Failed headers retain default value: "Not decoded."

## Message Part Walking

The `walk_eml()` function (libeml2pdf.py:146-233) iterates through all MIME parts of an email message.

### Part Classification

For each part, the function examines:

1. **Content-Disposition**: `None`, `inline`, or `attachment`
2. **Content-Type**: `text/plain`, `text/html`, `image/*`, etc.
3. **Payload**: The actual content bytes

### Processing Logic by Part Type

#### Text Content (Plain and HTML)

**Conditions** (libeml2pdf.py:185-186):
```python
if (content_type == 'text/plain' or content_type == 'text/html') and \
   (content_disposition is None or content_disposition == 'inline'):
```

**Processing**:
1. Decode payload using `decode_to_str()` (libeml2pdf.py:188)
2. If `text/plain`: Append to `plain_text_content` (libeml2pdf.py:190-191)
3. If `text/html`: Append to `html_content` (libeml2pdf.py:192-193)

**Note**: Multiple text parts are concatenated together. This handles multipart/alternative messages where both plain text and HTML versions exist.

#### Attachments and Inline Files

**Conditions** (libeml2pdf.py:196-197):
```python
elif (content_disposition == 'attachment' or
      content_disposition == 'inline'):
```

**Classification Logic** (libeml2pdf.py:199-208):

1. **Marked as attachment**: Always saved to attachment list
2. **Marked as inline + NOT an image**: Saved to attachment list
   - This handles inline non-image files like `.doc`, `.xls`, `.pdf`
3. **Marked as inline + IS an image**: Used for rendering, optionally saved

**Attachment Metadata** (libeml2pdf.py:210-216):
- Filename (HTML-decoded)
- File size (in bytes)
- MD5 hash

**Inline Images** (libeml2pdf.py:218-229):
- Extract Content-ID (CID)
- Store in `cid_attachments` dictionary with:
  - Filename
  - Binary content
  - Content-Type
- Used later for embedding via `embed_imgs()`

#### Skipped Parts

Parts are skipped if:
- No payload exists (libeml2pdf.py:177-178)
- Payload is not bytes (libeml2pdf.py:181-182)
- Does not match any classification above

### Final Assembly

After walking all parts (libeml2pdf.py:231-232):

```python
html_content = embed_imgs(html_content, cid_attachments) \
    if html_content else markdown(plain_text_content)
```

**Logic**:
1. If HTML content exists:
   - Embed inline images by replacing `cid:` references with data URIs
2. If only plain text exists:
   - Convert to HTML using Markdown parser

## Decoding Strategy

### The decode_to_str() Function (libeml2pdf.py:117-143)

This function implements a robust decoding strategy for converting bytes to strings.

#### Strategy Steps

**1. Strict Decoding Attempt** (libeml2pdf.py:126-127):
```python
try:
    decoded = bytes_content.decode(content_charset)
```

Uses the charset specified in the MIME part's Content-Type header.

**2. Fallback with Error Replacement** (libeml2pdf.py:128-131):
```python
except (UnicodeDecodeError, LookupError):
    logger.warning(f"Strict decode failed for {content_charset}. Using 'replace' mode.")
    decoded = bytes_content.decode(content_charset, errors='replace')
```

**Error Scenarios**:
- `UnicodeDecodeError`: Byte sequence invalid for specified charset
- `LookupError`: Charset name is unknown or not supported

**Replace Mode**: Replaces invalid bytes with `�` (U+FFFD REPLACEMENT CHARACTER)

**3. Unicode Escape Handling** (libeml2pdf.py:133-141):
```python
unicode_escape_pattern = r'\\u[0-9a-fA-F]{4}|\\U[0-9a-fA-F]{8}'
try:
    if re.search(unicode_escape_pattern, decoded):
        decoded = decoded.encode('utf-8').decode('unicode-escape')
except Exception as e:
    logger.debug(f"Unicode escape decoding skipped: {e}")
```

**Purpose**: Some email clients encode Unicode characters as escape sequences (e.g., `\u00a0` for non-breaking space).

**Process**:
- Detect patterns like `\u0000` or `\U00000000`
- Re-encode as UTF-8 and decode as `unicode-escape`
- If this fails (e.g., binary noise that looks like escapes), keep the 'replace' version

#### Charset Detection

Charsets come from the MIME part header (libeml2pdf.py:173):
```python
content_charset = part.get_content_charset() or 'utf-8'
```

**Default**: If no charset is specified, defaults to `utf-8`.

**Common Charsets**:
- `utf-8` - Universal Unicode encoding
- `iso-8859-1` - Latin-1 (Western European)
- `windows-1252` - Windows Western European
- `us-ascii` - 7-bit ASCII
- `gb2312`, `big5` - Chinese encodings
- `iso-2022-jp`, `shift_jis` - Japanese encodings

## Image Embedding

### The embed_imgs() Function (libeml2pdf.py:104-114)

Inline images in HTML emails are referenced using Content-ID (CID) URIs.

**Process**:
1. For each CID attachment collected during message walking
2. Base64-encode the image bytes
3. Create a data URI: `data:{content_type};base64,{encoded_data}`
4. Replace all `cid:{cid}` references in HTML with the data URI

**Example**:
```
Before: <img src="cid:image001@example.com">
After:  <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...">
```

This allows images to be embedded directly in the PDF without external references.

## Attachment List Generation

### The generate_attachment_list() Function (libeml2pdf.py:328-344)

Creates an HTML table summarizing all attachments.

**Columns**:
- **Name**: Filename (HTML-escaped)
- **Size**: Human-readable size using `hurry.filesize`
- **MD5sum**: Hex digest for integrity verification

**Example Output**:
```
Attachments:
Name              Size     MD5sum
document.pdf      1.2 MB   a1b2c3d4e5f6...
spreadsheet.xls   256 kB   f6e5d4c3b2a1...
```

## Complete Processing Flow Detail

### Step-by-Step: process_eml() (libeml2pdf.py:347-379)

**1. Open and Parse** (libeml2pdf.py:352-353):
```python
with open(eml_path, "r") as f:
    msg = email.message_from_file(f)
```

**2. Extract Header** (libeml2pdf.py:355):
```python
email_header = Header(msg, eml_path)
```
- Decodes from/to/subject/date fields
- Creates HTML table representation

**3. Walk Message Parts** (libeml2pdf.py:356):
```python
html_content, attachments = walk_eml(msg, eml_path)
```
- Extracts and decodes text content
- Collects attachment metadata
- Embeds inline images

**4. Generate Attachment List** (libeml2pdf.py:357):
```python
attachment_list = generate_attachment_list(attachments)
```

**5. Assemble Complete HTML** (libeml2pdf.py:360-370):
```python
if html_content:
    html_content = f"""
<meta charset="UTF-8">
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
{email_header.html}
{attachment_list}
<hr>
{html_content}
"""
```

**Structure**:
- UTF-8 meta tags
- Email header table (from/to/date/subject)
- Attachment list table
- Horizontal rule separator
- Email body content

**6. Generate Output Path** (libeml2pdf.py:372-374):
```python
output_path = get_output_base_path(email_header.date,
                                   email_header.subject,
                                   output_dir)
```

Format: `{date}-{subject}.pdf` (e.g., `2024-01-15-Meeting_Notes.pdf`)

**7. Generate PDF** (libeml2pdf.py:375-376):
```python
generate_pdf(html_content, output_path, eml_path,
             debug_html=debug_html, page=page, unsafe=unsafe)
```

This is where HTML sanitization occurs (unless `--unsafe` is specified).

## Edge Cases and Error Handling

### No Content

If no HTML or plain text content is found (libeml2pdf.py:378-379):
```python
else:
    logger.warning("No plain text or HTML content found in {eml_path}. Skipping...")
```

The file is skipped and no PDF is generated.

### Duplicate Filenames

The `get_exclusive_outfile()` function (libeml2pdf.py:259-284) handles filename conflicts:

1. Attempts to open file with exclusive creation (`'xb'` mode)
2. If file exists, increments counter: `filename_1.pdf`, `filename_2.pdf`, etc.
3. Ensures no race conditions in multiprocess mode

### Malformed Headers

Headers that cannot be decoded (libeml2pdf.py:59-61):
- Error is logged
- Field retains default value ("Not decoded.")
- Processing continues

### Invalid Charsets

Unknown or invalid charsets in decode_to_str():
- `LookupError` caught
- Fallback to 'replace' mode
- Invalid characters shown as `�`

### Multipart/Alternative

Emails with both plain text and HTML versions:
- Both are decoded and concatenated
- HTML takes precedence (libeml2pdf.py:231-232)
- Plain text is only converted to HTML if no HTML exists

## Multiprocessing Support

### Parallel Processing (libeml2pdf.py:382-409)

**Conditions for Multiprocessing**:
- `number_of_procs > 1`
- `verbose` is False
- Logger level is not DEBUG

**Reason for Limitations**:
Debug logging outputs long messages that are not multiprocess-safe and would get garbled.

**Implementation** (libeml2pdf.py:405-408):
```python
with Pool(number_of_procs) as p:
    p.starmap(process_eml, p_args)
```

Uses Python's `multiprocessing.Pool` for parallel processing of multiple EML files.

## Summary of Decoding Strategies

| Content Type | Decoding Strategy |
|--------------|-------------------|
| **Email Headers** | `email.header.decode_header()` → concatenate parts → HTML escape |
| **Text Content** | `decode_to_str()` with charset fallback and unicode escape handling |
| **Filenames** | `header_to_html()` (same as email headers) |
| **Image Bytes** | No decoding (kept as bytes) → Base64 encoded for data URI |
| **Attachment Bytes** | No decoding (only metadata stored) |

## Related Functions Reference

- `process_all_emls()` - Main entry point (libeml2pdf.py:382-409)
- `process_eml()` - Process single EML (libeml2pdf.py:347-379)
- `walk_eml()` - Extract content from parts (libeml2pdf.py:146-233)
- `decode_to_str()` - Robust bytes-to-string (libeml2pdf.py:117-143)
- `header_to_html()` - Decode and escape headers (libeml2pdf.py:82-101)
- `embed_imgs()` - Replace CID with data URIs (libeml2pdf.py:104-114)
- `generate_attachment_list()` - Create attachment table (libeml2pdf.py:328-344)
- `generate_pdf()` - HTML to PDF conversion (libeml2pdf.py:287-308)
- `get_output_base_path()` - Generate output filename (libeml2pdf.py:236-256)
- `get_exclusive_outfile()` - Handle file conflicts (libeml2pdf.py:259-284)
