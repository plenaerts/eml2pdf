"""Unittests for unique, exclusive file name functions."""
import unittest
from pathlib import Path
from shutil import rmtree
from os import mkdir
from eml_to_pdf import eml_to_pdf

test_dir = Path('tmp_test')


class ExclusiveFileTestCase(unittest.TestCase):
    def setUp(self):
        """Create 3 test files in test_dir"""
        basename = 'testfile'
        mkdir(test_dir)
        f = open(test_dir / Path(f'{basename}.pdf'), 'x')
        f.close()
        for i in range(1, 3):
            p = test_dir / Path(f'{basename}_{i}.pdf')
            f = p.open('x')
            f.close()

    def tearDown(self):
        """Cleanup test_dir"""
        rmtree(test_dir)

    def test_needs_increment(self):
        """An existing file should get an increment."""
        test_base_path = test_dir / Path('testfile.pdf')
        target_file_path = test_dir / Path('testfile_3.pdf')
        outfile = eml_to_pdf.get_exclusive_outfile(test_base_path)
        outfile.close()
        self.assertTrue(outfile.name == str(target_file_path))

    def test_needs_no_increment(self):
        """A non existing file should NOT get an increment."""
        test_base_path = test_dir / Path('testfile_unique.pdf')
        outfile = eml_to_pdf.get_exclusive_outfile(test_base_path)
        outfile.close()
        self.assertTrue(outfile.name == str(test_base_path))
