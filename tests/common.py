"""Common test data and utilities."""

from dataclasses import dataclass


@dataclass
class Eml:
    """Holds to, from, subject, msg in a specific encoding."""

    filename: str
    to: str
    _from: str
    subject: str
    msg: str
    enc: str


mails = [
    Eml(
        to='محمد أحمد <mohammed.ahmed@example.com>',
        _from='علي السعيد <>',
        subject='البريد الإلكتروني التجريبي',
        msg='مرحبًا، هذا بريد إلكتروني تجريبي.',
        enc='utf-8',
        filename='test_arabic.eml',
    ),
    Eml(
        to='鈴木 太郎 <taro.suzuki@example.com>',
        _from='山田 花子 <hanako.yamada@example.com>',
        subject='テストメール',
        msg='こんにちは、これはテストメールです。',
        enc='shift_jis',
        filename='test_shift-js.eml',
    ),
    Eml(
        to='王小明 <xiaoming.wang@example.com>',
        _from='李华 <li.hua@example.com>',
        subject='测试电子邮件',
        msg='你好，这是测试电子邮件。',
        enc='utf-8',
        filename='test_chinese.eml',
    ),
    Eml(
        to='Gérard Lévêque',
        _from='gerard.leveque@example.com',
        subject='E-mail de tâtonnement',
        msg="Bonjour, ceci est un e-mail de tâtonnement. C'est éclattant ça!",
        enc='iso-8859-1',
        filename='test_french.eml',
    ),
    Eml(
        to='山田 花子 <hanako.yamada@example.com>',
        _from='田中 一郎 <ichiro.tanaka@example.com>',
        subject='テストメール',
        msg='こんにちは、テストメールです。',
        enc='utf-8',
        filename='test_japanese-utf8.eml',
    ),
    Eml(
        to='Günther Müller <guenther.mueller@example.com>',
        _from='Jörg Weiß <joerg.weiss@example.com>',
        subject='Prüf-E-Mail',
        msg='Hello, this is a test email. Mit viel Spaß!',
        enc='utf-8',
        filename='test_german.eml',
    ),
]
