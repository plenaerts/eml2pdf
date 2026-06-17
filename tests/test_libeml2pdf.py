"""Unit tests for public functions in libeml2pdf module."""

import logging
import shutil
import tempfile
import unittest
from datetime import datetime
from email.message import EmailMessage
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from unittest.mock import patch

from eml2pdf import libeml2pdf

test_eml_path = Path('tests/test_data')


class TestProcessEml(unittest.TestCase):
    """Test the process_eml function."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_eml = test_eml_path / 'plain_text.eml'
        self.output_pdf = self.test_dir / 'output.pdf'

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_process_eml_basic(self):
        libeml2pdf.process_eml(self.test_eml, self.output_pdf)
        self.assertTrue(self.output_pdf.exists())
        self.assertGreater(self.output_pdf.stat().st_size, 0)


class TestProcessEmlBytes(unittest.TestCase):
    """Test the process_eml_bytes function."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_eml = test_eml_path / 'plain_text.eml'
        self.output_pdf = self.test_dir / 'output.pdf'

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_process_eml_basic(self):
        # First, process the eml as a file as usual.
        libeml2pdf.process_eml(self.test_eml, self.output_pdf)
        self.assertTrue(self.output_pdf.exists())
        self.assertGreater(self.output_pdf.stat().st_size, 0)

        # Now process the raw bytes and ensure they match
        pdf_bytes = self.test_eml.read_bytes()
        file_output = self.output_pdf.read_bytes()
        bytes_output = libeml2pdf.process_eml_bytes(pdf_bytes)
        self.assertEqual(file_output, bytes_output)


class TestProcessAllEmlsInDir(unittest.TestCase):
    """Test the process_all_emls_in_dir function."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.input_dir = test_eml_path / 'input'
        self.output_dir = self.test_dir / 'output'
        self.output_dir.mkdir()

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_process_all_emls_in_dir_basic(self):
        """Test processing multiple EML files in a directory."""
        # Process all EMLs
        libeml2pdf.process_all_emls_in_dir(self.input_dir, self.output_dir)

        # Check that PDF files were created
        eml_files = list(self.input_dir.glob('*.eml'))
        pdf_files = list(self.output_dir.glob('*.pdf'))
        # TODO: Isn't the input dir empty, and doesn't that falsifie this
        #       test?
        self.assertEqual(len(eml_files), len(pdf_files))

        # Check that all PDFs have content
        for pdf_file in pdf_files:
            self.assertGreater(pdf_file.stat().st_size, 0)


class TestSetLogLevels(unittest.TestCase):
    """Test the _set_log_levels function."""

    def setUp(self):
        """Set up test environment."""
        self.logger = libeml2pdf.logger
        self.orig_level = self.logger.level

    def tearDown(self):
        """Restore original logger level."""
        self.logger.setLevel(self.orig_level)

    def test_notset_defaults_to_warning(self):
        """When logger level is NOTSET, it should default to WARNING."""
        self.logger.setLevel(logging.NOTSET)
        libeml2pdf._set_log_levels()
        self.assertEqual(self.logger.level, logging.WARNING)

    def test_debug_sets_weasyprint_to_warning(self):
        """When DEBUG, weasyprint/fontTools should be WARNING."""
        self.logger.setLevel(logging.DEBUG)
        libeml2pdf._set_log_levels()
        wp_logger = logging.getLogger('weasyprint')
        self.assertEqual(wp_logger.level, logging.WARNING)

    def test_info_sets_weasyprint_to_error(self):
        """When INFO/WARNING, weasyprint/fontTools should be ERROR."""
        for level in [logging.INFO, logging.WARNING]:
            with self.subTest(level=level):
                self.logger.setLevel(level)
                libeml2pdf._set_log_levels()
                wp_logger = logging.getLogger('weasyprint')
                self.assertEqual(wp_logger.level, logging.ERROR)

    def test_error_sets_weasyprint_above_error(self):
        """When ERROR, weasyprint/fontTools should be ERROR+10."""
        self.logger.setLevel(logging.ERROR)
        libeml2pdf._set_log_levels()
        wp_logger = logging.getLogger('weasyprint')
        self.assertEqual(wp_logger.level, logging.ERROR + 10)

    def test_unexpected_level_raises(self):
        """Unexpected log level should raise ValueError."""
        # TODO: Need to rework libeml2pdf._set_log_levels a bit
        #       It doesn't take CRITICAL into account.
        self.logger.setLevel(logging.CRITICAL)
        with self.assertRaises(ValueError):
            libeml2pdf._set_log_levels()


class TestHeaderToHtml(unittest.TestCase):
    """Test header_to_html function for RFC 2047 encoded headers."""

    def test_plain_ascii_header(self):
        """Plain ASCII headers should be escaped properly."""
        result = libeml2pdf.header_to_html('Test <test@example.com>')
        self.assertEqual(result, 'Test &lt;test@example.com&gt;')

    def test_encoded_header(self):
        """RFC 2047 encoded headers should be decoded."""
        result = libeml2pdf.header_to_html('=?utf-8?B?SGVsbG8gV29ybGQ=?=')
        self.assertEqual(result, 'Hello World')

    def test_multipart_encoded_header(self):
        """Multi-part encoded headers should be concatenated."""
        encoded_header = '=?utf-8?B?SGVsbG8=?= =?utf-8?B?V29ybGQ=?='
        result = libeml2pdf.header_to_html(encoded_header)
        self.assertEqual(result, 'HelloWorld')

    def test_header_with_special_chars(self):
        """Headers with special characters should be escaped."""
        result = libeml2pdf.header_to_html('Test & Special <Chars>')
        self.assertEqual(result, 'Test &amp; Special &lt;Chars&gt;')

    def test_empty_header(self):
        """Empty header should return empty string."""
        result = libeml2pdf.header_to_html('')
        self.assertEqual(result, '')

    def test_utf8_header(self):
        """UTF-8 header should be decoded correctly."""
        result = libeml2pdf.header_to_html('=?utf-8?Q?Caf=C3=A9?=')
        self.assertEqual(result, 'Café')

    def test_header_with_quotes(self):
        """Headers with quotes should be escaped."""
        result = libeml2pdf.header_to_html('"Test Header"')
        self.assertEqual(result, '&quot;Test Header&quot;')


class TestDecodeToStr(unittest.TestCase):
    """Test _decode_to_str function."""

    def test_utf8_decoding(self):
        """UTF-8 bytes should decode correctly."""
        result = libeml2pdf._decode_to_str(b'Hello World', 'utf-8', '7bit')
        self.assertEqual(result, 'Hello World')

    def test_iso_8859_1_decoding(self):
        """ISO-8859-1 bytes should decode correctly."""
        result = libeml2pdf._decode_to_str(b'Hello', 'iso-8859-1', '7bit')
        self.assertEqual(result, 'Hello')

    def test_invalid_utf8_fallback(self):
        """Invalid UTF-8 should fall back to replace mode."""
        result = libeml2pdf._decode_to_str(b'\xff\xfe', 'utf-8', '7bit')
        self.assertIn('�', result)

    def test_unicode_escape_handling(self):
        """Unicode escape sequences in decoded bytes."""
        # The function handles unicode escapes in decoded strings
        # Test with unicode escape that would appear after decoding
        result = libeml2pdf._decode_to_str(b'\\u00a0', 'utf-8', '8bit')
        # Returns literal string because not processed in this case
        self.assertEqual(result, '\\u00a0')

    def test_8bit_cte_workaround(self):
        """8bit CTE should use UTF-8 decoding workaround."""
        # TODO: this would be more intereseting with a smiley :-)
        #       Check for value added on top of test_unicode_escape_handling()
        result = libeml2pdf._decode_to_str(b'Hello World', 'utf-8', '8bit')
        self.assertEqual(result, 'Hello World')

    def test_empty_bytes(self):
        """Empty bytes should return empty string."""
        result = libeml2pdf._decode_to_str(b'', 'utf-8', '7bit')
        self.assertEqual(result, '')

    def test_non_bytes_input(self):
        """Non-bytes input should return empty string."""
        result = libeml2pdf._decode_to_str('not bytes', 'utf-8', '7bit')
        self.assertEqual(result, '')

        # TODO: do we need the empty bytes with 8bit CTE or is that hogwash?


class TestEmbedImgs(unittest.TestCase):
    """Test _embed_imgs function."""

    def test_embed_single_image(self):
        """Single CID image should be embedded as data URI."""
        html = '<img src="cid:image1">'
        attachments = {
            'image1': {
                'filename': 'image.png',
                'content': b'fake_image_data',
                'content_type': 'image/png',
            }
        }
        result = libeml2pdf._embed_imgs(html, attachments)
        self.assertIn('data:image/png;base64,', result)
        self.assertNotIn('cid:image1', result)

    def test_embed_multiple_images(self):
        """Multiple CID images should all be embedded."""
        html = '<img src="cid:img1"><img src="cid:img2">'
        attachments = {
            'img1': {
                'filename': 'img1.png',
                'content': b'data1',
                'content_type': 'image/png',
            },
            'img2': {
                'filename': 'img2.jpg',
                'content': b'data2',
                'content_type': 'image/jpeg',
            },
        }
        result = libeml2pdf._embed_imgs(html, attachments)
        self.assertIn('data:image/png;base64,', result)
        self.assertIn('data:image/jpeg;base64,', result)
        self.assertNotIn('cid:img1', result)
        self.assertNotIn('cid:img2', result)

    def test_embed_with_empty_html(self):
        """Empty HTML should return empty string."""
        result = libeml2pdf._embed_imgs('', {})
        self.assertEqual(result, '')

    def test_embed_with_no_attachments(self):
        """HTML without attachments should be unchanged."""
        html = '<img src="cid:image1">'
        result = libeml2pdf._embed_imgs(html, {})
        self.assertEqual(result, html)


class TestGetCte(unittest.TestCase):
    """Test _get_cte function."""

    def test_get_cte_standard(self):
        """Standard Content-Transfer-Encoding should be extracted."""
        msg = EmailMessage()
        msg['Content-Transfer-Encoding'] = 'base64'
        result = libeml2pdf._get_cte(msg)
        self.assertEqual(result, 'base64')

    def test_get_cte_missing(self):
        """Missing CTE should return empty string."""
        msg = EmailMessage()
        result = libeml2pdf._get_cte(msg)
        self.assertEqual(result, '')

    def test_get_cte_with_parameters(self):
        """CTE with parameters should be stripped."""
        msg = EmailMessage()
        msg['Content-Transfer-Encoding'] = '8bit'
        result = libeml2pdf._get_cte(msg)
        self.assertEqual(result, '8bit')

    def test_get_cte_case_insensitive(self):
        """CTE should be case-insensitive."""
        msg = EmailMessage()
        msg['Content-Transfer-Encoding'] = 'BASE64'
        result = libeml2pdf._get_cte(msg)
        self.assertEqual(result, 'base64')


class TestGetOutputBasePath(unittest.TestCase):
    """Test _get_output_base_path function."""

    def test_with_date_and_subject(self):
        """Output path should include formatted date and subject."""
        result = libeml2pdf._get_output_base_path(
            datetime(2024, 1, 15, 10, 30), 'Meeting Notes', Path('/tmp/output')
        )
        expected = Path('/tmp/output/2024-01-15-Meeting_Notes.pdf')
        self.assertEqual(result, expected)

    def test_without_date(self):
        """Output path should use 'nodate' prefix when date is None."""
        # TODO We should maybe think about this. Do we want mails w/o dates?
        #      We probably need a test w/o date and the exclusive filenames.
        result = libeml2pdf._get_output_base_path(
            None, 'Test', Path('/tmp/output')
        )
        self.assertIn('nodate-Test.pdf', str(result))

    def test_special_chars_removed(self):
        """Special characters should be removed from filename."""
        result = libeml2pdf._get_output_base_path(
            datetime(2024, 1, 15),
            'Meeting: Notes <with> special|chars*and?quotes"',
            Path('/tmp/output'),
        )
        filename = str(result)
        self.assertNotIn(':', filename)
        self.assertNotIn('<', filename)
        self.assertNotIn('>', filename)
        self.assertNotIn('|', filename)
        self.assertNotIn('*', filename)
        self.assertNotIn('?', filename)
        self.assertNotIn('"', filename)

    def test_spaces_replaced_with_underscores(self):
        """Spaces should be replaced with underscores."""
        result = libeml2pdf._get_output_base_path(
            datetime(2024, 1, 15),
            'Meeting Notes With Spaces',
            Path('/tmp/output'),
        )
        self.assertIn('2024-01-15-Meeting_Notes_With_Spaces.pdf', str(result))

    def test_empty_subject(self):
        """Empty subject should work."""
        # TODO this test shows a dash at the end. That's not expected :-)
        result = libeml2pdf._get_output_base_path(
            datetime(2024, 1, 15), '', Path('/tmp/output')
        )
        self.assertIn('2024-01-15-.pdf', str(result))

    def test_underscores_preserved(self):
        """Underscores in subject should be preserved."""
        result = libeml2pdf._get_output_base_path(
            datetime(2024, 1, 15), 'File_Name', Path('/tmp/output')
        )
        self.assertIn('File_Name', str(result))


class TestGetExclusiveOutfile(unittest.TestCase):
    """Test _get_exclusive_outfile function."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_no_conflict(self):
        """File should be created when no conflict exists."""
        output_path = self.test_dir / 'test.pdf'
        outfile = libeml2pdf._get_exclusive_outfile(output_path)
        self.assertEqual(outfile.name, str(output_path))
        outfile.close()

    def test_with_conflict(self):
        """File should be incremented when conflict exists."""
        existing = self.test_dir / 'test.pdf'
        existing.touch()

        outfile = libeml2pdf._get_exclusive_outfile(existing)
        self.assertIn('_1.pdf', outfile.name)
        outfile.close()

    def test_multiple_conflicts(self):
        """File should increment properly with multiple conflicts."""
        # Create test.pdf, test_1.pdf, test_2.pdf to test increment logic
        for i in range(3):
            path = self.test_dir / (f'test_{i}.pdf' if i > 0 else 'test.pdf')
            path.touch()

        outfile = libeml2pdf._get_exclusive_outfile(self.test_dir / 'test.pdf')
        # The function starts with test.pdf, finds it exists, tries test_1.pdf
        # (exists), then test_2.pdf (exists), then test_3.pdf (doesn't exist)
        self.assertIn('_3.pdf', outfile.name)
        outfile.close()

    def test_creates_file(self):
        """File should be created and writable."""
        output_path = self.test_dir / 'writable.pdf'
        outfile = libeml2pdf._get_exclusive_outfile(output_path)
        outfile.write(b'test content')
        outfile.close()
        self.assertTrue(output_path.exists())
        self.assertEqual(output_path.read_bytes(), b'test content')


class TestEmailAndHeaderClasses(unittest.TestCase):
    """Test internal class initialization."""

    def test_email_class_with_msg(self):
        """Test _Email class can be instantiated with a message."""
        # TODO: add a test with weird encodings
        msg = EmailMessage()
        msg.set_content('Test content')
        msg['From'] = 'test@example.com'
        msg['Subject'] = 'Test'

        email_obj = libeml2pdf._Email(msg)
        self.assertIsNotNone(email_obj.header)
        self.assertIsNotNone(email_obj.html)
        self.assertIsInstance(email_obj.attachments, list)

    def test_header_unicode_error_handling(self):
        """Test _Header handles UnicodeError in header decoding."""
        msg = EmailMessage()
        msg['From'] = 'test@example.com'
        msg['Subject'] = 'Test'

        with patch('eml2pdf.libeml2pdf.header_to_html') as mock_html:
            mock_html.side_effect = UnicodeError('test', b'', 0, 1, 'error')
            with self.assertLogs('eml2pdf.libeml2pdf', level='ERROR'):
                header = libeml2pdf._Header(msg, 'test_id')
                self.assertEqual(header.from_addr, 'Not decoded.')


class TestCreateAttachment(unittest.TestCase):
    """Test _create_attachment function."""

    def test_none_filename_returns_none(self):
        """Test that None filename returns None."""
        result = libeml2pdf._create_attachment(None, b'content')
        self.assertIsNone(result)

    def test_valid_attachment_creation(self):
        """Test attachment creation with valid filename."""
        result = libeml2pdf._create_attachment('test.txt', b'content')
        self.assertIsNotNone(result)
        self.assertEqual(result.name, 'test.txt')
        self.assertGreater(result.size, 0)
        self.assertIsNotNone(result.md5sum)
        # TODO how about assertEquals on b'content' md5sum?


class TestGenerateAttachmentList(unittest.TestCase):
    """Test _generate_attachment_list function."""

    def test_with_attachments(self):
        """Test HTML table generation with attachments."""
        attachment1 = libeml2pdf._Attachment('file1.txt', 1024, 'abc123')
        attachment2 = libeml2pdf._Attachment('file2.pdf', 2048, 'def456')

        result = libeml2pdf._generate_attachment_list(
            [attachment1, attachment2]
        )

        self.assertIn('<table', result)
        self.assertIn('file1.txt', result)
        self.assertIn('file2.pdf', result)
        self.assertIn('abc123', result)
        self.assertIn('def456', result)
        self.assertIn('Attachments:', result)

    def test_empty_list(self):
        """Test empty list returns empty string."""
        result = libeml2pdf._generate_attachment_list([])
        self.assertEqual(result, '')


class TestProcessEmlErrorHandling(unittest.TestCase):
    """Test process_eml error handling."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_unicode_decode_error_fallback(self):
        """Test UnicodeDecodeError triggers UTF-8 fallback."""
        eml_content = b'Content-Type: text/plain\n\nHello World'
        eml_path = self.test_dir / 'test.eml'
        eml_path.write_bytes(eml_content)

        output_path = self.test_dir / 'output.pdf'

        libeml2pdf.process_eml(eml_path, output_path)
        self.assertTrue(output_path.exists())

    def test_process_eml_creates_pdf_from_eml_with_attachments_only(self):
        """Test PDF created even for EML with only attachments."""
        msg = MIMEMultipart()
        msg['From'] = 'test@example.com'
        msg['Subject'] = 'Test'
        part = MIMEApplication(b'attachment content')
        part.add_header(
            'Content-Disposition', 'attachment', filename='test.txt'
        )
        msg.attach(part)

        eml_path = self.test_dir / 'no_content.eml'
        with open(eml_path, 'wb') as f:
            f.write(msg.as_bytes())

        output_path = self.test_dir / 'output.pdf'

        # PDF should be created from headers even with no text/html content
        libeml2pdf.process_eml(eml_path, output_path)
        self.assertTrue(output_path.exists())


class TestGeneratePdfAdvanced(unittest.TestCase):
    """Test generate_pdf advanced scenarios."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generate_pdf_returns_none_for_file(self):
        """Test that generate_pdf returns None when writing to file."""
        output_path = self.test_dir / 'test.pdf'
        result = libeml2pdf.generate_pdf(
            html_content='<html><body><p>Test</p></body></html>',
            outfile_path=output_path,
        )
        self.assertIsNone(result)
        self.assertTrue(output_path.exists())

    def test_generate_pdf_returns_bytes_without_file(self):
        """Test that generate_pdf returns bytes when no outfile_path."""
        result = libeml2pdf.generate_pdf(
            html_content='<html><body><p>Test</p></body></html>'
        )
        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), 0)

    def test_generate_pdf_debug_html_creates_html_file(self):
        """Test that debug_html=True creates HTML file."""
        output_path = self.test_dir / 'test.pdf'
        libeml2pdf.generate_pdf(
            html_content='<html><body><p>Test</p></body></html>',
            outfile_path=output_path,
            debug_html=True,
        )

        html_path = self.test_dir / 'test.pdf.html'
        self.assertTrue(html_path.exists())
        self.assertIn('<html>', html_path.read_text())
