import unittest
from pathlib import Path
import email
from html import escape
from eml_to_pdf import eml_to_pdf
from . import generate_test_emls


eml_path = Path('tests/test_data')

# These mails definitions are used to generate emls in test data
mails = {m.filename: m for m in generate_test_emls.mails}

# Adding two extra email msgs. They are real eml's.
more_mails = mails | {
    "simple_plain_and_html_embedded_img.eml":
    generate_test_emls.TestMail(
        _from="First Last <first.last@outlook.com>",
        to="\"Last, First\" <first.last@outlook.com>",
        subject="This is a test mail with embedded imgs",
        msg="",
        enc="utf-8",
        filename="simple_plain_and_html_embedded_img.eml"
    ),
    "train_ticket.eml": generate_test_emls.TestMail(
        to="first.last@outlook.com",
        _from="\"NMBS/SNCB:\" <no-reply@belgiantrain.be>",
        subject="NMBS Mobile Ticket NL",
        msg="",
        enc="utf-8", filename="train_ticket.eml"
    ),
}


class TestEmls(unittest.TestCase):
    def test_headers(self):
        """Headers should remain the same from src data and eml files."""
        for eml in eml_path.glob('*.eml', case_sensitive=None):
            with open(eml) as f:
                eml_msg = email.message_from_file(f)
            src_eml = more_mails.get(eml.name)
            if not src_eml:
                continue
            with self.subTest(eml=eml):
                # Header fields are not named consistently. Tuples the contain
                # header attr names depending on context.
                for h in [('_from', 'from'),
                          ('to', 'to'),
                          ('subject', 'subject')
                          ]:
                    src_head = escape(getattr(src_eml, h[0]))
                    eml_head = eml_to_pdf.header_to_html(eml_msg.get(h[1]))
                    assert src_head == eml_head


if __name__ == '__main__':
    unittest.main()
