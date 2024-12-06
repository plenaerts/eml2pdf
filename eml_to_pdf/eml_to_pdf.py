import os
import email
import email.utils
import email.header
from html import escape
import re
import argparse
import datetime
from pathlib import Path
import sys
import base64

from weasyprint import HTML  # type: ignore

options = {"quiet": True, "load-error-handling": "skip", "encoding": "UTF-8"}


class Header:
    """Parsed eml header data and html rendering."""
    from_addr = "Not decoded."
    to_addr = "Not decoded."
    subject = "Not decoded."
    html = "Not decoded."
    date = None

    def __init__(self, msg: email.message.Message, eml_path: Path):
        # Format email header
        # Decode headers if encoded
        try:
            self.from_addr = header_to_html(msg.get("from", "No sender"))
            self.to_addr = header_to_html(msg.get("to", "No recipient"))
            self.subject = header_to_html(msg.get("subject", "No subject"))
        except UnicodeError as e:
            print(f"Failed to decode header field for {eml_path}: {str(e)}")

        self.date = email.utils.parsedate_to_datetime(msg.get("date", ""))
        self.formatted_date = self.date.strftime("%Y-%m-%d, %H:%M") \
            if self.date else "No date"

        self.html = f"""
        <table style="font-family: serif; margin-bottom: 20px;">
        <tr><td>from:</td><td>{self.from_addr}</td></tr>
        <tr><td>to:</td><td>{self.to_addr}</td></tr>
        <tr><td>date:</td><td>{self.formatted_date}</td></tr>
        <tr><td>subject:</td><td>{self.subject}</td></tr>
        </table>
        <hr>
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


def html_from_eml(msg: email.message.Message, eml_path: Path) -> str:
    """Extract HTML content from mail"""
    html_content = ""
    attachments = {}

    for part in msg.walk():
        content_disposition = part.get_content_disposition()
        content_type = part.get_content_type()
        if content_type == "text/html" and not content_disposition:
            payload = part.get_payload(decode=True)
            # Try multiple encodings if UTF-8 fails
            if isinstance(payload, bytes):
                # encs is a set of common western encodings.
                # Add systems default as another option.
                # TODO: add an argument for additional encodings.
                encs = {"utf-8", "latin1", "iso-8859-1", "cp1252"}
                encs.add(sys.getdefaultencoding())
                for encoding in encs:
                    try:
                        html_content = payload.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:  # If no encoding worked
                    print(
                        f"Failed to decode {eml_path} with common "
                        "encodings. Skipping..."
                    )
                    continue
            else:
                # This should never happen if decode=True above.
                html_content = str(payload)
        elif (content_disposition == 'attachment' or \
                            content_disposition == 'inline') and \
                            content_type.startswith('image/'):
            filename = part.get_filename()
            cid = part.get('Content-ID')
            content = part.get_payload(decode=True)

            # Store attachments by CID or filename
            if cid:
                cid = cid.strip('<>')
                attachments[cid] = {
                    'filename': filename,
                    'content': content,
                    'content_type': content_type
                }

    # Embed images in HTML
    if html_content:
        for cid, attachment in attachments.items():
            content_type = attachment['content_type']
            content = base64.b64encode(attachment['content']).decode('utf-8')
            data_uri = f"data:{content_type};base64,{content}"

            # Replace CID references in HTML
            html_content = html_content.replace(f"cid:{cid}", data_uri)
    return html_content


def get_output_path(date: datetime.datetime,
                    subject: str, output_dir: str) -> str:
    """Return a filename from date, subject and output_dir content"""
    # Format date for filename prefix
    file_date = date.strftime("%Y-%m-%d") if date else "nodate"

    # Create sanitized subject for filename
    safe_subject = re.sub(r'[<>:"/\\|?*]', "", subject)  # Remove illegal chars
    safe_subject = safe_subject.replace(
        " ", "_"
    )  # Replace spaces with underscores

    # Create base output filename
    base_filename = f"{file_date}-{safe_subject}.pdf"
    output_path = os.path.join(output_dir, base_filename)

    # Add number suffix if file exists
    counter = 1
    while os.path.exists(output_path):
        base_filename = f"{file_date}-{safe_subject}_{counter}.pdf"
        output_path = os.path.join(output_dir, base_filename)
        counter += 1
    return output_path


def generate_pdf(html_content: str, output_path: str, filename: str):
    """Convert HTML to PDF"""
    try:
        html = HTML(string=html_content)
        html.write_pdf(output_path)
#                pdfkit.from_string(html_content, output_path, options=options)
        print(f"Converted {filename} to PDF successfully.")
    except OSError as e:
        print(f"Failed to convert {filename}: {str(e)}")
        # Optionally, try again with images disabled
        try:
            # TODO: this is not going to work, since weasyprint has
            # different options...
            options["load-error-handling"] = "ignore"
            options["no-images"] = True
            # pdfkit.from_string(html_content, output_path,
            #                    options=options)
            print(f"Converted {filename} to PDF successfully "
                  "(without images).")
        except Exception as e2:
            print(f"Second attempt failed for {filename}: {str(e2)}")


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Convert EML files to PDF")
    parser.add_argument("input_dir", help="Directory containing EML files")
    parser.add_argument("output_dir", help="Directory for PDF output")
    args = parser.parse_args()

    # Create output directory if it doesn't exist
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # Process all .eml files in input directory
    for filename in os.listdir(args.input_dir):
        if not filename.lower().endswith(".eml"):
            continue

        eml_path = os.path.join(args.input_dir, filename)

        # Open and parse the .eml file
        with open(eml_path, "r") as f:
            msg = email.message_from_file(f)

        email_header = Header(msg, eml_path)
        html_content = html_from_eml(msg, eml_path)

        # Convert to PDF if HTML content is found
        if html_content:
            # Add UTF-8 meta tag and email header if not present
            if isinstance(html_content, str):
                html_content = f"""
                    <meta charset="UTF-8">
                    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
                    {email_header.html}
                    {html_content}
                """

            output_path = get_output_path(email_header.date,
                                          email_header.subject,
                                          args.output_dir)
            generate_pdf(html_content, output_path, filename)
        else:
            print(f"No HTML content found in {filename}. Skipping...")

    print("All .eml files processed.")


if __name__ == "__main__":
    main()
