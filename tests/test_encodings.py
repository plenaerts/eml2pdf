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
    "plain_lorem_ipsum.eml": generate_test_emls.TestMail(
        to="recipient@example.com",
        _from="sender@example.com",
        subject="Test Email with Lorem Ipsum",
        msg="",
        enc="utf-8", filename="plain_lorem_ipsum.eml"
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

    def test_plain_text(self):
        """Plain text file body should render as html."""
        pt_emls = [('plain_lorem_ipsum.eml',
'''<p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
<p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
<p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
<p>Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
<p>Curabitur pretium tincidunt lacus. Nulla gravida orci a odio. Nullam varius, turpis et commodo pharetra, est eros bibendum elit, nec luctus magna felis sollicitudin mauris.</p>'''
                    ),
                   ('plain_text.eml',
'''<p>This message is plain text and contains some smileys:</p>
<p>😀</p>
<p>😅</p>
<p>😇</p>'''
                    ),
                   ('mixed_plain_html_smiley_embedded.eml',
'''<!DOCTYPE html><html><head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>Mixed content</title>
  </head>
  <body>
    <p>This is an email saved as both HTML and plain text.</p>
    <p>HTML contains some <b>formatting!</b></p>
    <h1>And even a Heading!<br>
    </h1>
    <p>And an emoji in both embedded <img src="data:image/png;base64,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" alt="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEgAAABICAYAAABV7bNHAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAADwFJREFUeNrsnHuMHVUdx39n5r7v3e3tdru7sNJe2xKVil2QGnl2eZU/0LBgTAxSKf8Q0Ji2KtFoQtt/JCSSQhBQiGmRYvQfWmIxEQNdVB6GRLZgEaWFbaHbx9Ld2+7d+545/n5nzsw9M3fuc3dlxT3J6Tkzs3dmzud8f7/znAIshIWwEOYwsPnwEpnfrBrAN0k6JzhA4tZDw/9XgDK7V6VAgwHGGMFYh/kUphiZ9RbeN0FIYFLKRzFPcYSb/ACeG0ncdmjkEwEo89TKAdDY7UyDIdBZCiNQxGORiqdrFUB4BTlwC44dTW6BwpQbmBcRRhHWMOafTWw4vPd/ClDm1yuTeNfNAkwAoQSw2BgpFXAIjOYGUzM4oCxIFUAIq4xpSaRphLcLrz+U+Nbh0XkLCMGkMNmKEDayIN42qIFIbUA2GOWpjKkHHjAyw9VjG5gh1YSAAEFxAlU06fwuvL59NkGxWVEMkGJgK0MogFBYSKYESDUh5lBxP5nVUZAndZkgmZ4AZFpqQki8yC1QAFsQVPpjBYRwBjHZiSpJERQWwtuFpXKkj3GgMOWJHjh1+fhAss2Oe0EJQHhQENDSeO0OhLT3YwGEcHaQrxGqIShhqZyAZUouMEpUrcpRE9RoxZw8ryQ+kXNeMT1SEIEqUCTfNTM1sTZNaj/+coAJMDYgTTpfKrcbDHPyHiVBE066Sj0cbCurdAUURdExmVtBQsoL30TdgqvbgcTagqNJOBHdghNiFTBaHTBeFTXzdA5u9fiZmamoyZT0ytwBJCBRa2dBGpkTQH5wWMRyxgKO7Yw1qPY9mgcK8zgfVkc9qnJsR+01M9PjjwicKU0uPzNIrGWzikg4UQmHSTg2GM2tGKapYCotGGvBxLiPiblAmT5qMm1IYCkpZ6iQPt2suQWaBLnH8TkRza0c5gNHVZECjDGo0Zp5mn61+eLytAOFOXnm8kdMHIu8aXVEZb/c8o/233Izicraj6cvaqbgWhPq2YbJILVWtkN2lGPD0CQcjTn5yjFTjmXUmXKNetdgRfu3uqVKoUznb8Fzb/fz7Ipg8nn2dWtYY0Fitr/Eyj77q3P2zNjEZD9nvxgixPDmUel3NMWs7CZdU5p3VTUeE2PMo55mWzGX7/GYmep37GNTPZZ57AIIU8uZYObLUEh/sL17U3nbTBS0QxRSkLeiCw6rDcdb0+6atZWkXNOVKNVlXa/8ra00r6LUZzoNhaYc2z4xaHVkgcoS1CEQ6dw6vgNSbQFC9WzGZECYFspSmJcOLgW4zMr7YlqtYxVYxQS84JhWMbPKAFdC0aECkUG1STEVFLgq1XIVTKSB2GI8r+9s2cRkq/U+PjApTCsmTUuvNOfMzwdozA1Kafad1o610wPzmhl3WituKqN9r0mZ3rzsJ1FHchpNLWtA6ewElLITVy/dAsOtKGgIY5IFLdJMbbFYHQfpB0dRDLAWOoh+VWk7aW/jwJR38fo6VcH2ORoOhSxTC0QX0d03tWpiWwWAoIy627kyz/jKsX8/OMzzgrMxvPZ0TJm3UXDB83RYbQuQsw3ki/RQfKiWLwr4mNcAJikm53Fs9bj7Mj4jdebu+zz1u0nY8/szkJk2xX3XXBiFu+9cAitXhNtmc/JkGR594iN45dVpcZyIa3D9NR2w4RuLIYEdV04vgCZE78DFe3HXe3G1UsmvBajLwkEPx8EoTpOKtjSjoNsdGdJIXa8ekbs6gT79kp89PA5P/XbSgUPhwFs5+MGPxuDwe4W24dz13Q8cOKIy8f5UCdvvO1lb2T7jQdtE7Qk9PZKw3UpTJjYkCmpPk8q5YvAdeLpfgPJvHszD8y9OQX93FG5Y2wvXXtzjKtBjj59uCxApJ5/ncNnqJeK+q/oTFfj/yMHz+6fcvrFWpXpUZFmJDlognEIzG6gLSE6bppj9Q73BA3yuPYM1SmF5b8yyYbxXV0fIpaRWVURgSTmdsSB0xCyvsLgj6PqbP72YcZu9Vr9z6liAnA7WglG6MthIQYOOeckuvt/4ifkoyc5PS7PKFQyRTmXLMDFVrCpwK8EGmisazrkjJ7OuvyEVNVQMVJuc6GNhebWQ8I3rGjnpNQ593TMt4c0znykMjCdOlcSN3jiUhmhYd0DNRqB7vfD3UyJfNrhPC2c5ZibHs9535X7DHLuHHgg2paABq6fq6beAZyTuGY2rtdLXG3QVaLYDgfGDQy2aW+01KtbbRWaWpUgFJdEPJesCUsdWfv3tqpUJzxzPyhWhhoVstamnLgIBqBcuuzRePZXiN3upTPu6OpMBvSKSOoCSDpyq5RlW7eSgWrK33JSsW5D113U0LKxfuGWo8X1VAMxvMKUWSVVWnU6s5ttTZR4ItcZOPi/S2xuAe7b01FTO3Xd2t2VaG25dXIHgCfQ8Uln1TGWDNThHSbJroFf7oYBr7sfx7qz2kJbVOsdctUkv/MyzaWyBihBPaHD5l+M1C9hssEG8/No0TGdMURn2sxoOxW1H7VfZstyaHgDDKDWYcvVOrEMNufq9i3KdXr5dtTQypYagfRXDPCsBnq5LjfI1dgZshtfnU2D1rxmFXBuA+Ayvz6fAW7+mAkq7F+Uqv+JNPIDPJ1jcL8/rT8Q1mg8Si2nOhDhvTJeWwI9NQu7QSSi8Nw7Gmdy8YGNki1D8cAJy7+J7jY4DLxuVBcda5aEJyXy2yXUx7p7eZH4rDDTG+tu7YEy5oWixEAS7ExBYinFRFPRF0TkHYiKQMlZOeTwDpY8yVRWVxwpMfOl87CkHa6qLNj9ww+n1D9cDNAomT9nLKAKPip1buApHxwWc0MohiF60Ccyzo1D68CWMw3htFOOEc0MCRuC0eEgA02gGD1OaYmhpiIGFp0AQOA5aCQSB4aXKcIaFk/hON0DwU+uwkgbEO2Vf2wb5f49B7PPL1bXIyj9ymcgsFppS0ChySTF7X6CPJImbkbYmrdilDyKA5SIfvmCjVaMC1jDW6AGMIyJft2Gh5RcfpZGpkDrqLgsjBIr60jUIZVDk1UDn6PniHbhSAC8oLK+Zt5Tnnbz3AnoJwQyK7W00dcmZa32cybwWCcHbx3V44KtXwNc2fBvWD30T+s5dZl3rTAlY6miLoBkYCRgvnMGYFvl6QY9g7JJ5vCfd1yr0OqEUL4yqOaSpM/DHvU+D9vYxuKpfVxoeryuxymoW85YFNVDQiLOkYqgyZK68Fo84L/Hko/eJePk1X4HLr71RpImORW7fJAtINTrX4eUX92F8TsCh8PWLixBYHa+oxbuNxiC1ZoGbZpX/8QM0bO+tAakiTiNdzxJwcEknrD7vuM+L7cPc3Q6sNWuvdJQ1V4EqiZ574PW/wssv7BPHarjgnDIEe/uq9xnZmxmwnEYmU7GgeoBoSwiOyUbwRwMEiRly4kxt1Siv6xDq74alHRkYn9Jq1OI+ke/rX+aAorQXj9uFRoU//M5bcOidN+Hwv2SKx/VCb3cAAlihlYYH3Gv6WM5y5oxvC+bfzAM8icoRgGgvMs380yYSxx9xy8zC/UugJ5lFQPULdeLYUYxPy6P7nPMErvfc5c7xqs9e6JgmgTikFDwzlW4IolZYdkm/z+YHcPY0lqembPMaQQc92gygvfjjHcLMyrS/T66Be2+OKrpiXRcc3D3R1otb4I5W5pRf/8usm99lX4xhlyJeUY9n0ycJoJyerAijmfkguQl7mNsbtEvc9QCu2O/Q+k74wuci83LYlYhp8D2aTailHiyfMTUNhtWDpmHWruYmzKzwEMhFfhEN7nqAmr93U4+w8/kW7v9JH8Rpw4V3P5Hc5EkVX5r4yLEaNK9004Dk5utRS0GmoyLOedVHJvGoBvdu7hE1Nl/C91E5K84L+ez0qKinPJkGI+eMv7bX7IzWec4dePP9tCsLAqZcZbUnndBxa/YeQQYrloXg/h/3wQ9/egIy2dbWvFYvOQdSnV0QD7on8g+ePg6jZ0/DdKnYMpzrrki4N3aqvoeGFfkyFMdPOnD8nHNT013px7v3ByIdgywWFLtaaQseIa3a1SqPp3OmgHT4SLEhlMHzzoe1vcsRTP1VkNdPHIHn3j8ogDXyOfdu6YELPxOp3oZnq1/ueM2/f8RWj9jxWsu8GgKipejS9Pgbwc6eZCt7FHfvScPuZ6qfSTC+s+YqWNu3vGWzIVCPHPizr6KoodiKZh6Lag33KBaOnYDSpNPy3oxw9s5ownTysc4hLPWeULLH2htNkEKsNiSpqveOFuEX2AV48595RzX3XHJdQ8XUCwRn26t/EKYnOoFLA3DXbV1w6cWx6j3SXlDod0rjk1A47ijxQYSzZaYzziJMPJLYgYXfHF7SZ5kafYIQamKfNKYE6JXXijAUuHFGcFRIDxzeA+uvjcD1VyaUbXhQeysemlZpfAIKYw4c6hQ2tU+66Sn30w+Hd7JAeGO4u7etnfbmdBTKx5aCcSqJcTHwYmtdA70nDYHeSQj0j4OWnGppp71QzthYZUAOcHU9v9P2msTphyNvMF0fCHX3gUaOO+KB1MK3GuZkB5jZKKaJ2i8Xz4MWzwk47X2rgW5n7BS2WONtwWlr0YaUhL/aGEJz0xPR9r72qbXTlfnPF7tG4Z65nFpf+/CCAfnRo2BMZ9uG0/aqFvkks5TdHOhcDKEl2J2PqJvMawCZze/FwGtebljlybNQ+GDMO898c6tw2gZkt25GKUdqSoaXopo64x/7F4c8X4T8kTFUzbR6J+oIbmu3nDNaF6W9NJoe2mkaxSE9EoNgd7cFqtlvVlkTAqr5zaoCplCC4vFTOLZKu2dHcTSAcGb0nxDMysLx6Z9HB7lZ3smNUooFgxBc3AXBriSwsO7aazTbXz2X01NQOnUajIxLMWmpmgdno2yzurKOvmmjaRS2EijRNHd0oCOPQWBRp5job+e7eVAnAssGGFNZMM6cFXAUH2ODeUh2ANOzVaY52XqQ/mXXYDl/9nZUlfikQTxI10GPx7B7EAEtFEJ1BZ20SjhYcDOXF3yMTBb7TEUwsnnrXHUgB/wkQtk1F2WZ2/+7Y/fKZGHyQzQ/4yYsLaWp2eAvobwk53FG57IM/9XNK+knulKlzARBGmR6YDk3ygIY07RBOS/sdbJpGQ/INauRmTrdhbAQFsJCWAifoPAfAQYAon8+5y7atbsAAAAASUVORK5CYII=" class="transparent" moz-do-not-send="false" width="72" height="72"> and unicode form ð</p>
  </body>
</html>'''
                    )]
        for eml in pt_emls:
            with open(eml_path / Path(eml[0])) as f:
                eml_msg = email.message_from_file(f)
            with self.subTest(eml=eml[0]):
                eml_html = eml_to_pdf.html_from_eml(eml_msg, eml[0])
                assert eml_html == eml[1]


if __name__ == '__main__':
    unittest.main()
