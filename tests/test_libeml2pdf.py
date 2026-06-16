"""Unit tests for public functions in libeml2pdf module."""

import logging
import shutil
import tempfile
import unittest
from pathlib import Path

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
        self.logger.setLevel(logging.CRITICAL)
        with self.assertRaises(ValueError):
            libeml2pdf._set_log_levels()
