#!/usr/bin/env python3
"""Generate test EML files for testing."""

import sys
from pathlib import Path

# Add tests directory to path to import common
sys.path.insert(0, str(Path(__file__).parent.parent))

from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate

from tests.common import mails


def main():
    # Create a directory to save the EML files
    output_dir = Path('test_data')
    output_dir.mkdir(exist_ok=True, parents=True)

    # Generate EML files with encoded headers
    for m in mails:
        # Create a MIME message
        msg = MIMEMultipart()
        msg['From'] = Header(m._from, m.enc).encode()
        msg['To'] = Header(m.to, m.enc).encode()
        msg['Subject'] = Header(m.subject, m.enc).encode()
        msg['Date'] = formatdate(localtime=True)

        # Attach text with the specified encoding
        text = MIMEText(m.msg, 'plain', m.enc)
        msg.attach(text)

        # Save the EML file
        file_path = output_dir / m.filename
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(msg.as_string())


if __name__ == '__main__':
    main()
