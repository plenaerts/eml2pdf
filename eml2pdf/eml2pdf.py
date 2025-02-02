import email
import email.utils
import email.header
from html import escape
import re
import argparse
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

logging.basicConfig()
logger = logging.getLogger(__name__)


def get_args() -> argparse.Namespace:
    """Construct arguments for CLI script."""
    parser = argparse.ArgumentParser(description="Convert EML files to PDF")
    parser.add_argument("input_dir", type=Path,
                        help="Directory containing EML files")
    parser.add_argument("output_dir", type=Path,
                        help="Directory for PDF output")
    parser.add_argument("-d", "--debug_html", action="store_true",
                        help="Write intermediate html file next to pdf's")
    parser.add_argument("-n", "--number-of-procs", metavar='number', type=int,
                        default=len(os.sched_getaffinity(0)),
                        help="Number of parallel processes. Defaults to "
                        "the number of available logical CPU's to eml_to_pdf.")
    parser.add_argument("-p", "--page", metavar="size", default='a4',
                        help="a3 a4 a5 b4 b5 letter legal or ledger with "
                        "or without 'landscape', for example: 'a4 landscape' "
                        "or 'a3' including quotes. Defaults to 'a4', implying "
                        "portrait.")
    parser.add_argument("--unsafe", action="store_true", default=False,
                        help="Don't sanitize HTML from potentially unsafe "
                        "elements such as remote images, scripts, etc. This "
                        "may expose sensitive user information.")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show a lot of verbose debugging info. Forces '
                        'number of procs to 1.')
    args = parser.parse_args()
    return args


@dataclass
class Attachment:
    """Attachment name, size and md5 hash."""
    name: str
    size: int
    md5sum: str


class Email:
    """Parsed eml file with header, attachments, rendered html."""
    def __init__(self, msg: email.message.Message, eml_path: Path):
        self.header = Header(msg, eml_path)
        self.html, self.attachments = walk_eml(msg, eml_path)


class Header:
    """Parsed eml header data and html rendering."""
    from_addr = "Not decoded."
    to_addr = "Not decoded."
    subject = "Not decoded."
    html = "Not decoded."
    formatted_date = "No date."
    date = None

    def __init__(self, msg: email.message.Message, eml_path: Path):
        """Parse msg and set from, to, subject, date and html payload."""
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
    """Return decoded, concatenated eml header, html encoded."""
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
    """Return html with embedded images from attachments."""
    if html_content:
        for cid, attachment in attachments.items():
            content_type = attachment['content_type']
            content = base64.b64encode(attachment['content']).decode('utf-8')
            data_uri = f"data:{content_type};base64,{content}"

            # Replace CID references in HTML
            html_content = html_content.replace(f"cid:{cid}", data_uri)
    return html_content


def decode_to_str(bytes_content: bytes, content_charset: str) -> str:
    """Smart decode unicode bytes to str."""
    logger.debug(f'bytes: {str(bytes_content)}')
    logger.debug(f'charset: {content_charset}')
    if isinstance(bytes_content, bytes):
        decoded = bytes_content.decode(content_charset)
        logger.debug(f'decoded: {decoded}')
        unicode_escape_pattern = r'\\u[0-9a-fA-F]{4}|\\U[0-9a-fA-F]{8}'
        if re.search(unicode_escape_pattern, decoded):
            decoded = decoded.encode('utf-8').decode('unicode-escape')
            logger.debug(f'unicode escaped decoded : {decoded}')
    else:
        decoded = 'Decoding error!'
    return decoded


def walk_eml(msg: email.message.Message, eml_path: Path) -> \
        tuple[str, list[Attachment]]:
    """Extract HTML content from mail.

    * msg:   Email message to parse
    * eml_path: Path of the file being parsed. To display messages.

    *return: tuple of html content and attachment list.

    For every part in the eml, if there is a payload and it is plain text
    html or an image, decode that part.

    Append decoded plain text and html payloads together.

    Keep a list of image attachments or inline images with a content id. Use
    that list to insert them in the resulting html.

    Create a list of attachments.
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

        payload = bytes(payload)
        if ((content_type == 'text/plain' or content_type == 'text/html')
                and not content_disposition):
            decoded_payload = decode_to_str(payload, content_charset)
        if decoded_payload == 'Decoding error!':
            logger.error(f"{eml_path} not decoded correctly.")
        if content_type == 'text/plain' and not content_disposition:
            plain_text_content += decoded_payload
        elif content_type == "text/html" and not content_disposition:
            html_content += decoded_payload
        elif (content_disposition == 'attachment' or
              content_disposition == 'inline'):
            filename = part.get_filename()
            # Do stuff to save all attachments.
            if content_disposition == 'attachment' and filename:
                filename = header_to_html(filename)
                filesize = sys.getsizeof(payload)
                _hash = hashlib.md5()
                _hash.update(payload)
                attachments.append(Attachment(name=filename, size=filesize,
                                              md5sum=_hash.hexdigest()))
            if content_type.startswith('image/'):
                # Only extract attached or inline images.
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
    """Return a filename from date, subject and output_dir.

    Do not check if this filename exists or is writable. This should
    be done later.
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
    """Return an exclusively opened file object for outfile_path.

    Take the outfile_path as a basename and increment a counter if the
    filename is not available for exclusive writing.

    Binary mode for weasyprint's HTML.write_pdf().

    We have a pool of email processors whose data may point to the same output
    file. A process must be sure a filename is and remains available.
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
    """Convert HTML to PDF."""
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
    """Return case insensitive *.eml glob in input_dir."""
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
    """Main worker function to generate a pdf from an eml."""
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


def main():
    # Set up argument parser
    args = get_args()
    if args.unsafe:
        logger.warning('WARNING! Not trying to '
                       'sanitize HTML. This may expose sensitive user '
                       'information.')

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Create output directory if it doesn't exist
    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        logger.error(f'Could not create output directory {args.output_dir}.')
        sys.exit(1)

    # Process all .eml files in input directory
    eml_file_paths = get_filepaths(args.input_dir)
    # Don't use multiprocessing if n is 1 or we output debug logging.
    # We output a lot of long debug messages. That's not multiprocess safe.
    # Messages would get garbled.
    if args.number_of_procs == 1 or args.verbose or \
            logger.level == logging.DEBUG:
        for ep in eml_file_paths:
            process_eml(ep, Path(args.output_dir), args.page, args.debug_html,
                        args.unsafe)
    else:
        p_args = ((ep, Path(args.output_dir), args.page, args.debug_html,
                   args.unsafe)
                  for ep in eml_file_paths)
        with Pool(args.number_of_procs) as p:
            p.starmap(process_eml, p_args)

    print("All .eml files processed.")


if __name__ == "__main__":
    main()
