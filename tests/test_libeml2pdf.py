"""Unit tests for public functions in libeml2pdf module."""
import unittest
import tempfile
from pathlib import Path
import shutil

from eml2pdf import libeml2pdf

test_eml_path = Path('tests/test_data')

class TestProcessEml(unittest.TestCase):
    """Test the process_eml function."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_eml = test_eml_path / 'plain_text.eml'
        self.output_pdf = self.test_dir / "output.pdf"

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
        self.output_pdf = self.test_dir / "output.pdf"

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
        self.input_dir = test_eml_path / "input"
        self.output_dir = self.test_dir / "output"
        self.output_dir.mkdir()

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_process_all_emls_in_dir_basic(self):
        """Test processing multiple EML files in a directory."""
        # Process all EMLs
        libeml2pdf.process_all_emls_in_dir(self.input_dir, self.output_dir)

        # Check that PDF files were created
        eml_files = list(self.input_dir.glob("*.eml"))
        pdf_files = list(self.output_dir.glob("*.pdf"))
        self.assertEqual(len(eml_files), len(pdf_files))

        # Check that all PDFs have content
        for pdf_file in pdf_files:
            self.assertGreater(pdf_file.stat().st_size, 0)
