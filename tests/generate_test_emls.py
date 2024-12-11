from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formatdate
from pathlib import Path
from dataclasses import dataclass


@dataclass
class TestMail:
    '''Holds to, from, subject, msg in a specific encoding.'''
    filename: str
    to: str
    _from: str
    subject: str
    msg: str
    enc: str


mails = [
    TestMail(to="محمد أحمد <mohammed.ahmed@example.com>",
             _from="علي السعيد <>",
             subject="البريد الإلكتروني التجريبي",
             msg="مرحبًا، هذا بريد إلكتروني تجريبي.",
             enc="utf-8", filename="test_arabic.eml"
             ),
    TestMail(
        to="鈴木 太郎 <taro.suzuki@example.com>",
        _from="山田 花子 <hanako.yamada@example.com>",
        subject="テストメール",
        msg="こんにちは、これはテストメールです。",
        enc="shift_jis", filename="test_shift-js.eml"
    ),
    TestMail(
        to="王小明 <xiaoming.wang@example.com>",
        _from="李华 <li.hua@example.com>",
        subject="测试电子邮件",
        msg="你好，这是测试电子邮件。",
        enc="utf-8", filename="test_chinese.eml"
    ),
    TestMail(
        to="Gérard Lévêque",
        _from="gerard.leveque@example.com",
        subject="E-mail de tâtonnement",
        msg="Bonjour, ceci est un e-mail de tâtonnement. "
        "C'est éclattant ça!",
        enc="iso-8859-1", filename="test_french.eml"
    ),
    TestMail(
        to="山田 花子 <hanako.yamada@example.com>",
        _from="田中 一郎 <ichiro.tanaka@example.com>",
        subject="テストメール",
        msg="こんにちは、テストメールです。",
        enc="utf-8", filename="test_japanese-utf8.eml"
    ),
    TestMail(
        to="Günther Müller <guenther.mueller@example.com>",
        _from="Jörg Weiß <joerg.weiss@example.com>",
        subject="Prüf-E-Mail",
        msg="Hello, this is a test email. Mit viel Spaß!",
        enc="utf-8", filename="test_german.eml"
    )
]


def main():
    # Create a directory to save the EML files
    output_dir = Path("test_data")
    output_dir.mkdir(exist_ok=True, parents=True)

    # Generate EML files with encoded headers
    file_paths = []
    for m in mails:
        # Create a MIME message
        msg = MIMEMultipart()
        msg["From"] = Header(m._from, m.enc).encode()
        msg["To"] = Header(m.to, m.enc).encode()
        msg["Subject"] = Header(m.subject, m.enc).encode()
        msg["Date"] = formatdate(localtime=True)

        # Attach text with the specified encoding
        text = MIMEText(m.msg, "plain", m.enc)
        msg.attach(text)

        # Save the EML file
        file_name = Path(m.filename)
        file_path = output_dir / file_name
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(msg.as_string())
        file_paths.append(file_path)


if __name__ == '__main__':
    main()
