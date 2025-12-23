import email
import email.utils
import email.header
from html import escape
import re
import datetime
from pathlib import Path
import base64
import sys
import fnmatch
import os
from io import BufferedWriter
import logging
from multiprocessing import Pool
import hashlib
from dataclasses import dataclass

from weasyprint import HTML, CSS  # type: ignore
from markdown import markdown
from hurry.filesize import size  # type: ignore

from . import security

logger = logging.getLogger(__name__)


@dataclass
class Attachment:
    """Attachment metadata extracted from an email message.

    Attributes:
        name (str): Filename of the attachment (HTML-decoded and escaped).
        size (int): Size of the attachment in bytes.
        md5sum (str): MD5 hash hex digest for integrity verification.
    """
    name: str
    size: int
    md5sum: str


class Email:
    """Parsed EML file with header, attachments, and rendered HTML content.

    Encapsulates a complete parsed email message including metadata,
    HTML-rendered content, and attachment information.

    Attributes:
        header (Header): Parsed email header with from/to/subject/date fields.
        html (str): HTML-rendered email body content with embedded images.
        attachments (list[Attachment]): List of attachment metadata.

    Args:
        msg (email.message.Message): Parsed email message object.
        eml_path (Path): Path to the EML file being processed.

    Note:
        The constructor automatically extracts all content by calling
        Header() and walk_eml() internally.
    """
    def __init__(self, msg: email.message.Message, eml_path: Path):
        self.header = Header(msg, eml_path)
        self.html, self.attachments = walk_eml(msg, eml_path)


class Header:
    """Parsed email header data with HTML rendering.

    Extracts and formats email metadata from an email.message.Message object.
    Handles encoded headers and converts them to HTML-safe strings.

    Attributes:
        from_addr (str): Sender address. Defaults to "Not decoded." if parsing fails.
        to_addr (str): Recipient address. Defaults to "Not decoded." if parsing fails.
        subject (str): Email subject. Defaults to "Not decoded." if parsing fails.
        html (str): HTML table representation of the header fields.
        formatted_date (str): Human-readable date string in format "YYYY-MM-DD, HH:MM".
            Defaults to "No date" if date header is missing.
        date (datetime.datetime | None): Parsed datetime object from the Date header.
            None if date header is missing or unparseable.

    Note:
        Headers are decoded using email.header.decode_header() and HTML-escaped
        to prevent XSS vulnerabilities. UnicodeErrors during decoding are logged
        but don't stop processing.
    """
    from_addr = "Not decoded."
    to_addr = "Not decoded."
    subject = "Not decoded."
    html = "Not decoded."
    formatted_date = "No date."
    date = None

    def __init__(self, msg: email.message.Message, eml_path: Path):
        """Parse email message and extract header fields.

        Decodes From, To, Subject, and Date headers from the email message.
        Creates an HTML table representation of the header information.

        Args:
            msg (email.message.Message): The parsed email message object.
            eml_path (Path): Path to the EML file being processed (for logging).

        Note:
            If header decoding fails with UnicodeError, the error is logged
            and the field retains its default value ("Not decoded.").
        """
        # Format email header
        # Decode headers if encoded
        try:
            self.from_addr = header_to_html(msg.get("from", "No sender"))
            self.to_addr = header_to_html(msg.get("to", "No recipient"))
            self.subject = header_to_html(msg.get("subject", "No subject"))
        except UnicodeError as e:
            logger.error(f"Failed to decode header field for {eml_path}: "
                         f"{str(e)}")

        msg_date = msg.get("date", "")
        self.date = email.utils.parsedate_to_datetime(msg.get("date", "")) \
            if msg_date else None
        self.formatted_date = self.date.strftime("%Y-%m-%d, %H:%M") \
            if self.date else "No date"

        self.html = f"""
<table style="font-family: serif;
              margin-bottom: 20px;
              border-spacing: 1rem 0;
              text-align: left">
<tr><th scope="row">From:</th><td>{self.from_addr}</td></tr>
<tr><th scope="row">To:</th><td>{self.to_addr}</td></tr>
<tr><th scope="row">Date:</th><td>{self.formatted_date}</td></tr>
<tr><th scope="row">Subject:</th><td>{self.subject}</td></tr>
</table>
"""


def header_to_html(header_str: str) -> str:
    """Decode and HTML-escape an email header field.

    Processes encoded email headers by decoding multi-part headers and
    concatenating them into a single HTML-safe string.

    Decoding Strategy:
        1. Uses email.header.decode_header() to parse encoded headers
        2. Handles multi-part headers by concatenating them
        3. For string parts, uses them directly
        4. For byte parts, decodes with specified encoding (defaults to 'ascii' if None)
        5. HTML-escapes the final result to prevent XSS

    Args:
        header_str (str): The raw email header string (may be RFC 2047 encoded).

    Returns:
        str: Decoded and HTML-escaped header string safe for inclusion in HTML.

    Example:
        >>> header_to_html('=?utf-8?B?SGVsbG8gV29ybGQ=?=')
        'Hello World'
        >>> header_to_html('Test <tag>')
        'Test &lt;tag&gt;'
    """
    headers = email.header.decode_header(header_str)
    headers_as_string = ""
    # decoded headers can have multiple parts. Concat them.
    for head in headers:
        # If a header contains a str, don't try to decode.
        if isinstance(head[0], str):
            headers_as_string += head[0]
        else:
            # If a header is ascii encoded then head[1] is None
            if head[1] is None:
                enc = 'ascii'
            else:
                # If head[1] is not None it should be a string with the
                # encoding.
                enc = head[1]
            headers_as_string += str(head[0], enc)
    # eml headers can contain &, <, >
    return escape(headers_as_string)


def embed_imgs(html_content: str, attachments: dict) -> str:
    """Embed inline images into HTML by replacing CID references with data URIs.

    Converts Content-ID (CID) references in HTML to inline data URIs,
    allowing images to be embedded directly in the PDF without external references.

    Processing:
        1. For each CID attachment collected during message walking
        2. Base64-encode the image bytes
        3. Create a data URI: data:{content_type};base64,{encoded_data}
        4. Replace all cid:{cid} references in HTML with the data URI

    Args:
        html_content (str): HTML content potentially containing cid: image references.
        attachments (dict): Dictionary mapping CID to attachment data. Each value
            should have 'content' (bytes), 'content_type' (str), and 'filename' (str).

    Returns:
        str: HTML content with all CID references replaced by data URIs.

    Example:
        Before: <img src="cid:image001@example.com">
        After:  <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...">
    """
    if html_content:
        for cid, attachment in attachments.items():
            content_type = attachment['content_type']
            content = base64.b64encode(attachment['content']).decode('utf-8')
            data_uri = f"data:{content_type};base64,{content}"

            # Replace CID references in HTML
            html_content = html_content.replace(f"cid:{cid}", data_uri)
    return html_content


def decode_to_str(bytes_content: bytes, content_charset: str) -> str:
    """Robustly decode bytes to string with fallback handling.

    Implements a multi-stage decoding strategy to handle various email content
    encodings, including malformed or misidentified charsets.

    Decoding Strategy:
        1. **Strict Decoding**: Attempts to decode using the specified charset
        2. **Fallback with Replace**: If strict decoding fails, uses 'replace' mode
           to substitute invalid bytes with � (U+FFFD REPLACEMENT CHARACTER)
        3. **Unicode Escape Handling**: Detects and processes unicode escape sequences
           like \\u00a0 or \\U00000000 that some email clients use

    Error Handling:
        - UnicodeDecodeError: Byte sequence invalid for specified charset → fallback
        - LookupError: Charset name unknown or not supported → fallback
        - Exception during escape decoding: Keep the 'replace' version

    Args:
        bytes_content (bytes): The raw byte content to decode.
        content_charset (str): The character encoding name (e.g., 'utf-8', 'iso-8859-1').

    Returns:
        str: Decoded string content. May contain replacement characters (�) if
            original bytes were invalid for the specified encoding.

    Note:
        Common charsets: utf-8, iso-8859-1, windows-1252, us-ascii, gb2312, big5,
        iso-2022-jp, shift_jis

    Example:
        >>> decode_to_str(b'Hello', 'utf-8')
        'Hello'
        >>> decode_to_str(b'\\xff\\xfe', 'utf-8')  # Invalid UTF-8
        '��'
    """
    decoded = "" 
    
    if isinstance(bytes_content, bytes):
        logger.debug(f'bytes: {str(bytes_content)[:100]}...')
        logger.debug(f'charset: {content_charset}')
        
        try:
            # Attempt strict decoding
            decoded = bytes_content.decode(content_charset)
        except (UnicodeDecodeError, LookupError):
            # Fallback for binary data/mismatched charsets
            logger.warning(f"Strict decode failed for {content_charset}. Using 'replace' mode.")
            decoded = bytes_content.decode(content_charset, errors='replace')

        # Handle unicode escape patterns (e.g., \u00a0)
        unicode_escape_pattern = r'\\u[0-9a-fA-F]{4}|\\U[0-9a-fA-F]{8}'
        try:
            if re.search(unicode_escape_pattern, decoded):
                decoded = decoded.encode('utf-8').decode('unicode-escape')
                logger.debug(f'unicode escaped decoded : {decoded[:100]}...')
        except Exception as e:
            # If escape decoding fails (common in binary noise), keep the 'replace' version
            logger.debug(f"Unicode escape decoding skipped: {e}")
            
    return decoded


def walk_eml(msg: email.message.Message, eml_path: Path) -> \
        tuple[str, list[Attachment]]:
    """Extract and process all MIME parts from an email message.

    Walks through all parts of a MIME multipart email message, extracting text
    content, handling attachments, and embedding inline images.

    Part Classification:
        For each MIME part, examines:
        - Content-Disposition: None, 'inline', or 'attachment'
        - Content-Type: 'text/plain', 'text/html', 'image/*', etc.
        - Payload: The actual content bytes

    Processing by Part Type:
        **Text Content (plain/html)**:
            - Conditions: content_type is text/plain or text/html AND
              (content_disposition is None OR 'inline')
            - Processing: Decode using decode_to_str() and append to content strings
            - Note: Multiple text parts are concatenated (handles multipart/alternative)

        **Attachments and Inline Files**:
            - Conditions: content_disposition is 'attachment' OR 'inline'
            - Classification:
              1. Marked 'attachment': Always saved to attachment list
              2. Marked 'inline' + NOT image: Saved to attachment list (e.g., .doc, .xls)
              3. Marked 'inline' + IS image: Used for rendering, optionally saved
            - Metadata: Filename, size (bytes), MD5 hash

        **Inline Images**:
            - Extract Content-ID (CID) from headers
            - Store in cid_attachments with filename, binary content, content-type
            - Later embedded via embed_imgs() by replacing cid: references

    Final Assembly:
        - If HTML content exists: Embed inline images via embed_imgs()
        - If only plain text exists: Convert to HTML using Markdown parser
        - If no content: Returns empty string

    Args:
        msg (email.message.Message): The parsed email message to walk.
        eml_path (Path): Path to the EML file (used for logging messages).

    Returns:
        tuple[str, list[Attachment]]: A tuple of (html_content, attachments) where
            html_content is the rendered HTML and attachments is a list of
            Attachment objects with metadata.

    Note:
        Skips parts with no payload or non-bytes payloads.
    """
    html_content = ""
    plain_text_content = ""
    cid_attachments = {}
    attachments: list[Attachment] = list()

    for part in msg.walk():
        content_disposition = part.get_content_disposition()
        content_type = part.get_content_type()
        content_charset = part.get_content_charset() or 'utf-8'
        payload = part.get_payload(decode=True)

        # Go to the next part if we don't have a payload.
        if not payload:
            continue

        # Ensure payload is bytes (safety check)
        if not isinstance(payload, bytes):
            continue

        # We allow 'inline' here to capture text bodies marked as inline
        if (content_type == 'text/plain' or content_type == 'text/html') and \
           (content_disposition is None or content_disposition == 'inline'):
            
            decoded_payload = decode_to_str(payload, content_charset)
            
            if content_type == 'text/plain':
                plain_text_content += decoded_payload
            elif content_type == "text/html":
                html_content += decoded_payload

        # Handle Attachments AND Inline Files
        elif (content_disposition == 'attachment' or 
              content_disposition == 'inline'):
            
            filename = part.get_filename()
            is_image = content_type.startswith('image/')

            # Save as attachment if it is:
            # 1. Marked 'attachment' OR
            # 2. Marked 'inline' BUT is not an image (like your .doc file)
            should_save_as_attachment = (
                content_disposition == 'attachment' or 
                (content_disposition == 'inline' and not is_image)
            )

            if should_save_as_attachment and filename:
                filename = header_to_html(filename)
                filesize = sys.getsizeof(payload)
                _hash = hashlib.md5()
                _hash.update(payload)
                attachments.append(Attachment(name=filename, size=filesize,
                                              md5sum=_hash.hexdigest()))
            
            # Handle Inline Images (rendering)
            if is_image:
                cid = part.get('Content-ID')

                # Store attachments by CID or filename
                if cid:
                    cid = cid.strip('<>')
                    cid_attachments[cid] = {
                        'filename': filename,
                        'content': payload,
                        'content_type': content_type
                    }

    html_content = embed_imgs(html_content, cid_attachments) \
        if html_content else markdown(plain_text_content)
    return (html_content, attachments)


def get_output_base_path(date: datetime.datetime | None,
                         subject: str, output_dir: Path) -> Path:
    """Generate output PDF filename from email metadata.

    Creates a sanitized filename in the format: {date}-{subject}.pdf

    Sanitization:
        - Removes illegal filename characters: < > : " / \\ | ? *
        - Replaces spaces with underscores
        - Uses "nodate" prefix if date is None

    Args:
        date (datetime.datetime | None): Email date from header. None if not available.
        subject (str): Email subject line.
        output_dir (Path): Directory where the PDF will be saved.

    Returns:
        Path: Complete output path for the PDF file.

    Note:
        Does not check if the file exists or is writable. Use get_exclusive_outfile()
        to handle filename conflicts.

    Example:
        >>> get_output_base_path(datetime(2024, 1, 15), "Meeting Notes", Path("/out"))
        Path('/out/2024-01-15-Meeting_Notes.pdf')
    """
    # Format date for filename prefix
    file_date = date.strftime("%Y-%m-%d") if date else "nodate"

    # Create sanitized subject for filename
    safe_subject = re.sub(r'[<>:"/\\|?*]', "", subject)  # Remove illegal chars
    safe_subject = safe_subject.replace(
        " ", "_"
    )  # Replace spaces with underscores

    # Create base output filename
    base_filename = f"{file_date}-{safe_subject}.pdf"
    output_path = output_dir / Path(base_filename)

    return output_path


def get_exclusive_outfile(outfile_path: Path) -> BufferedWriter:
    """Open output file exclusively with automatic conflict resolution.

    Attempts to open the file with exclusive creation ('xb' mode). If the file
    already exists, automatically increments a counter suffix until an available
    filename is found: filename_1.pdf, filename_2.pdf, etc.

    Multiprocessing Safety:
        Uses exclusive creation to prevent race conditions when multiple processes
        try to write to the same filename. Ensures each process gets a unique file
        without overwriting.

    Args:
        outfile_path (Path): Desired output file path.

    Returns:
        BufferedWriter: Opened file object in binary write mode, ready for
            WeasyPrint's HTML.write_pdf() method.

    Note:
        File is opened in binary mode ('xb') for compatibility with WeasyPrint.
        The exclusive flag ensures no existing file is overwritten.

    Example:
        If "report.pdf" exists:
        >>> get_exclusive_outfile(Path("report.pdf"))
        <_io.BufferedWriter name='report_1.pdf'>
    """
    try:
        outfile = open(outfile_path, 'xb')
    except OSError:
        outfile = open(os.devnull, 'wb')
        outfile.close()  # We won't use devnull.

    counter = 1
    while outfile.name == os.devnull:
        new_outfile_path = Path(outfile_path.parent) / \
            Path(f"{outfile_path.stem}_{counter}{outfile_path.suffix}")
        try:
            outfile = open(new_outfile_path, 'xb')
        except OSError:
            counter += 1
    return outfile


def generate_pdf(html_content: str, outfile_path: Path, infile: Path,
                 debug_html: bool = False, page: str = 'a4',
                 unsafe: bool = False):
    """Convert HTML content to PDF with optional sanitization.

    Generates a PDF from HTML content using WeasyPrint. By default, sanitizes
    HTML to remove security and privacy risks before rendering.

    Processing Steps:
        1. Sanitize HTML (unless unsafe=True)
        2. Optionally save HTML to disk for debugging
        3. Parse HTML with WeasyPrint
        4. Apply page size and margins via CSS
        5. Get exclusive output file handle (prevents conflicts)
        6. Write PDF to file

    Args:
        html_content (str): The HTML content to convert to PDF.
        outfile_path (Path): Desired output file path.
        infile (Path): Input EML file path (for logging/messages).
        debug_html (bool, optional): If True, saves HTML to {outfile}.html for
            debugging. Defaults to False.
        page (str, optional): Page size for PDF (e.g., 'a4', 'letter').
            Defaults to 'a4'.
        unsafe (bool, optional): If True, bypasses HTML sanitization. Only use
            when you completely trust the source. Defaults to False.

    Note:
        HTML sanitization is performed by security.sanitize_html() unless
        unsafe=True. See security.md for details on what is filtered.

    Raises:
        Exception: Logs error if PDF generation fails, but does not re-raise.
    """
    if not unsafe:
        html_content = security.sanitize_html(html_content)
    try:
        if debug_html:
            html_file = outfile_path.parent / Path(outfile_path.name + '.html')
            of = open(html_file, 'w')
            of.write(html_content)
            of.close()
        html = HTML(string=html_content)
        css = CSS(string=f'@page {{ size: {page}; margin: 1cm }}')

        outfile = get_exclusive_outfile(outfile_path)

        html.write_pdf(outfile, presentational_hints=True,
                       stylesheets=[css])
        print(f"Converted {infile} to PDF successfully.")
    except Exception as e:
        logger.error(f"Failed to convert {infile}: {str(e)}")


def get_filepaths(input_dir: Path) -> list[Path]:
    """Find all EML files in directory with case-insensitive matching.

    Searches for files matching *.eml pattern (case-insensitive) in the input
    directory. Handles Python version differences for glob() case sensitivity.

    Args:
        input_dir (Path): Directory to search for EML files.

    Returns:
        list[Path]: List of paths to EML files found.

    Note:
        Uses case_sensitive parameter for Python 3.12+, falls back to manual
        filtering for earlier versions.
    """
    # case_sensitive is added to pathlib.Path.glob() in 3.12
    # Debian is at 3.11. We can remove this test when Debian reaches 3.12.
    eml_pat = '*.eml'
    if sys.version_info.minor >= 12:
        # Nice new syntax. Unpack the Generator returned by glob() in a list.
        filepaths = list(input_dir.glob(eml_pat, case_sensitive=None))
    else:
        # Ugly old syntax
        filepaths = [
                path for path in input_dir.glob("**/*")
                if fnmatch.fnmatchcase(path.name.lower(), eml_pat)
                ]
    return filepaths


def generate_attachment_list(attachments: list[Attachment]) -> str:
    """Generate HTML table summarizing email attachments.

    Creates an HTML table with columns for attachment name, human-readable size,
    and MD5 hash for integrity verification.

    Args:
        attachments (list[Attachment]): List of attachment metadata objects.

    Returns:
        str: HTML table string, or empty string if no attachments.

    Example Output:
        Attachments:
        Name              Size     MD5sum
        document.pdf      1.2 MB   a1b2c3d4e5f6...
        spreadsheet.xls   256 kB   f6e5d4c3b2a1...
    """
    html = ''
    if attachments:
        html += '<table style="font-family: serif; ' \
                              'margin-bottom: 20px;' \
                              'border-spacing: 1rem 0;' \
                              'text-align: left;">'
        html += '<thead><tr><th colspan="3">Attachments:</th></tr>' \
                '<tr><th scope="col">Name</th>' \
                '<th scope="col">Size</th>' \
                '<th scope="col">MD5sum</th></tr></thead>'
        for at in attachments:
            html += f'<tr><td>{at.name}</td><td>{size(at.size)}</td>' \
                    f'<td>{at.md5sum}</td></tr>'
        html += "</table>"

    return html


def process_eml(eml_path: Path, output_dir: Path, page: str = 'a4',
                debug_html: bool = False, unsafe: bool = False):
    """Process a single EML file and generate a PDF.

    Complete processing pipeline for converting an email message to PDF:
    1. Parse EML file with email.message_from_file()
    2. Extract header (from/to/subject/date)
    3. Walk message parts to extract content and attachments
    4. Generate attachment list table
    5. Assemble complete HTML with UTF-8 meta tags, header, attachments, and body
    6. Generate output filename from date and subject
    7. Convert to PDF (with sanitization unless unsafe=True)

    HTML Structure:
        - UTF-8 meta tags
        - Email header table (from/to/date/subject)
        - Attachment list table
        - Horizontal rule separator
        - Email body content (with embedded images)

    Args:
        eml_path (Path): Path to the EML file to process.
        output_dir (Path): Directory where PDF will be saved.
        page (str, optional): PDF page size. Defaults to 'a4'.
        debug_html (bool, optional): Save HTML to disk for debugging. Defaults to False.
        unsafe (bool, optional): Skip HTML sanitization. Defaults to False.

    Note:
        If no text content is found, the file is skipped and a warning is logged.
        Output filename format: {date}-{subject}.pdf
    """
    logging.info(f'Processing {eml_path}')
    # Open and parse the .eml file
    with open(eml_path, "r") as f:
        msg = email.message_from_file(f)

    email_header = Header(msg, eml_path)
    html_content, attachments = walk_eml(msg, eml_path)
    attachment_list = generate_attachment_list(attachments)

    # Convert to PDF if HTML content is found
    if html_content:
        # Add UTF-8 meta tag and email header if not present
        if isinstance(html_content, str):
            html_content = f"""
<meta charset="UTF-8">
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
{email_header.html}
{attachment_list}
<hr>
{html_content}
"""

        output_path = get_output_base_path(email_header.date,
                                           email_header.subject,
                                           output_dir)
        generate_pdf(html_content, output_path, eml_path,
                     debug_html=debug_html, page=page, unsafe=unsafe)
    else:
        logger.warning("No plain text or HTML content found "
                       f"in {eml_path}. Skipping...")


def process_all_emls(input_dir: Path, output_dir: Path, number_of_procs: int,
                     verbose: bool, debug_html: bool, page: str, unsafe: bool):
    """Process all EML files in a directory to PDFs with optional multiprocessing.

    Main entry point for batch processing of email files. Handles directory
    creation, file discovery, and parallel or sequential processing.

    Multiprocessing Conditions:
        Parallel processing is used when ALL of these are true:
        - number_of_procs > 1
        - verbose is False
        - logger level is not DEBUG

    Reason for Limitations:
        Debug logging outputs long messages that are not multiprocess-safe
        and would become garbled when multiple processes write simultaneously.

    Args:
        input_dir (Path): Directory containing EML files to process.
        output_dir (Path): Directory where PDFs will be saved (created if needed).
        number_of_procs (int): Number of parallel processes. Use 1 for sequential.
        verbose (bool): Enable verbose/debug logging.
        debug_html (bool): Save intermediate HTML files for debugging.
        page (str): PDF page size (e.g., 'a4', 'letter').
        unsafe (bool): Skip HTML sanitization (use only with trusted sources).

    Note:
        Creates output_dir with parents if it doesn't exist.
        Exits with code 1 if output directory cannot be created.
        Uses Python's multiprocessing.Pool for parallel processing.
    """
    if verbose:
        logger.level = logging.DEBUG

    # Create output directory if it doesn't exist
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        logger.error(f'Could not create output directory {output_dir}.')
        sys.exit(1)

    # Process all .eml files in input directory
    eml_file_paths = get_filepaths(input_dir)
    # Don't use multiprocessing if n is 1 or we output debug logging.
    # We output a lot of long debug messages. That's not multiprocess safe.
    # Messages would get garbled.
    if number_of_procs == 1 or verbose or \
            logger.level == logging.DEBUG:
        for ep in eml_file_paths:
            process_eml(ep, Path(output_dir), page, debug_html, unsafe)
    else:
        p_args = ((ep, Path(output_dir), page, debug_html, unsafe)
                  for ep in eml_file_paths)
        with Pool(number_of_procs) as p:
            p.starmap(process_eml, p_args)

    print("All .eml files processed.")
