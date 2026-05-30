"""Unit tests for CLI argument parsing and main function."""

import unittest
from unittest.mock import patch
from pathlib import Path
import logging
from eml2pdf.eml2pdf import get_args, main


class TestGetArgs(unittest.TestCase):
    """Test command-line argument parsing."""

    def test_convert_dir_basic_arguments(self):
        """Test parsing of required input_dir and output_dir arguments."""
        with patch('sys.argv', ['eml2pdf', 'convert_dir', 'input', 'output']):
            args = get_args()
            self.assertEqual(args.input_dir, Path('input'))
            self.assertEqual(args.output_dir, Path('output'))

    def test_convert_dir_debug_html_flag(self):
        """Test -d/--debug_html flag."""
        with patch(
            'sys.argv',
            ['eml2pdf', 'convert_dir', 'input', 'output', '--debug_html'],
        ):
            args = get_args()
            self.assertTrue(args.debug_html)

        with patch(
            'sys.argv', ['eml2pdf', 'convert_dir', 'input', 'output', '-d']
        ):
            args = get_args()
            self.assertTrue(args.debug_html)

    def test_convert_dir_debug_html_default(self):
        """Test debug_html defaults to False."""
        with patch('sys.argv', ['eml2pdf', 'convert_dir', 'input', 'output']):
            args = get_args()
            self.assertFalse(args.debug_html)

    def test_convert_dir_number_of_procs_flag(self):
        """Test -n/--number-of-procs flag."""
        with patch(
            'sys.argv',
            ['eml2pdf', 'convert_dir', 'input', 'output', '-n', '4'],
        ):
            args = get_args()
            self.assertEqual(args.number_of_procs, 4)

        with patch(
            'sys.argv',
            [
                'eml2pdf',
                'convert_dir',
                'input',
                'output',
                '--number-of-procs',
                '8',
            ],
        ):
            args = get_args()
            self.assertEqual(args.number_of_procs, 8)

    def test_convert_dir_number_of_procs_default(self):
        """Test number_of_procs has a default value."""
        with patch('sys.argv', ['eml2pdf', 'convert_dir', 'input', 'output']):
            args = get_args()
            # Should be set to CPU count, just verify it's a positive integer
            self.assertIsInstance(args.number_of_procs, int)
            self.assertGreater(args.number_of_procs, 0)

    def test_convert_dir_page_size_flag(self):
        """Test -p/--page flag."""
        with patch(
            'sys.argv',
            ['eml2pdf', 'convert_dir', 'input', 'output', '-p', 'letter'],
        ):
            args = get_args()
            self.assertEqual(args.page, 'letter')

        with patch(
            'sys.argv',
            ['eml2pdf', 'convert_dir', 'input', 'output', '--page', 'a3'],
        ):
            args = get_args()
            self.assertEqual(args.page, 'a3')

        with patch(
            'sys.argv',
            [
                'eml2pdf',
                'convert_dir',
                'input',
                'output',
                '-p',
                'a4 landscape',
            ],
        ):
            args = get_args()
            self.assertEqual(args.page, 'a4 landscape')

    def test_convert_dir_page_size_default(self):
        """Test page size defaults to 'a4'."""
        with patch('sys.argv', ['eml2pdf', 'convert_dir', 'input', 'output']):
            args = get_args()
            self.assertEqual(args.page, 'a4')

    def test_convert_dir_unsafe_flag(self):
        """Test --unsafe flag."""
        with patch(
            'sys.argv',
            ['eml2pdf', 'convert_dir', 'input', 'output', '--unsafe'],
        ):
            args = get_args()
            self.assertTrue(args.unsafe)

    def test_convert_dir_unsafe_default(self):
        """Test unsafe defaults to False."""
        with patch('sys.argv', ['eml2pdf', 'convert_dir', 'input', 'output']):
            args = get_args()
            self.assertFalse(args.unsafe)

    def test_convert_dir_verbose_flag(self):
        """Test -v/--verbose flag."""
        with patch(
            'sys.argv', ['eml2pdf', 'convert_dir', 'input', 'output', '-v']
        ):
            args = get_args()
            self.assertTrue(args.verbose)

        with patch(
            'sys.argv',
            ['eml2pdf', 'convert_dir', 'input', 'output', '--verbose'],
        ):
            args = get_args()
            self.assertTrue(args.verbose)

    def test_convert_dir_verbose_default(self):
        """Test verbose defaults to False."""
        with patch('sys.argv', ['eml2pdf', 'convert_dir', 'input', 'output']):
            args = get_args()
            self.assertFalse(args.verbose)

    def test_convert_dir_quiet_flag(self):
        """Test -q/--quiet flag."""
        with patch(
            'sys.argv', ['eml2pdf', 'convert_dir', 'input', 'output', '-q']
        ):
            args = get_args()
            self.assertTrue(args.quiet)

        with patch(
            'sys.argv',
            ['eml2pdf', 'convert_dir', 'input', 'output', '--quiet'],
        ):
            args = get_args()
            self.assertTrue(args.quiet)

    def test_convert_dir_quiet_default(self):
        """Test quiet defaults to False."""
        with patch('sys.argv', ['eml2pdf', 'convert_dir', 'input', 'output']):
            args = get_args()
            self.assertFalse(args.quiet)

    def test_convert_dir_combined_flags(self):
        """Test multiple flags can be combined."""
        with patch(
            'sys.argv',
            [
                'eml2pdf',
                'convert_dir',
                'input',
                'output',
                '-d',
                '-v',
                '--unsafe',
                '-n',
                '2',
                '-p',
                'letter',
            ],
        ):
            args = get_args()
            self.assertTrue(args.debug_html)
            self.assertTrue(args.verbose)
            self.assertTrue(args.unsafe)
            self.assertEqual(args.number_of_procs, 2)
            self.assertEqual(args.page, 'letter')
            self.assertFalse(args.quiet)

    def test_convert_file_basic_arguments(self):
        """Test parsing of required input_file and output_file arguments for convert_file."""
        with patch(
            'sys.argv', ['eml2pdf', 'convert_file', 'input.eml', 'output.pdf']
        ):
            args = get_args()
            self.assertEqual(args.input_file, Path('input.eml'))
            self.assertEqual(args.output_file, Path('output.pdf'))

    def test_convert_file_debug_html_flag(self):
        """Test -d/--debug_html flag for convert_file."""
        with patch(
            'sys.argv',
            [
                'eml2pdf',
                'convert_file',
                'input.eml',
                'output.pdf',
                '--debug_html',
            ],
        ):
            args = get_args()
            self.assertTrue(args.debug_html)

        with patch(
            'sys.argv',
            ['eml2pdf', 'convert_file', 'input.eml', 'output.pdf', '-d'],
        ):
            args = get_args()
            self.assertTrue(args.debug_html)

    def test_convert_file_debug_html_default(self):
        """Test debug_html defaults to False for convert_file."""
        with patch(
            'sys.argv', ['eml2pdf', 'convert_file', 'input.eml', 'output.pdf']
        ):
            args = get_args()
            self.assertFalse(args.debug_html)

    def test_convert_file_page_size_flag(self):
        """Test -p/--page flag for convert_file."""
        with patch(
            'sys.argv',
            [
                'eml2pdf',
                'convert_file',
                'input.eml',
                'output.pdf',
                '-p',
                'letter',
            ],
        ):
            args = get_args()
            self.assertEqual(args.page, 'letter')

        with patch(
            'sys.argv',
            [
                'eml2pdf',
                'convert_file',
                'input.eml',
                'output.pdf',
                '--page',
                'a3',
            ],
        ):
            args = get_args()
            self.assertEqual(args.page, 'a3')

    def test_convert_file_page_size_default(self):
        """Test page size defaults to 'a4' for convert_file."""
        with patch(
            'sys.argv', ['eml2pdf', 'convert_file', 'input.eml', 'output.pdf']
        ):
            args = get_args()
            self.assertEqual(args.page, 'a4')

    def test_convert_file_unsafe_flag(self):
        """Test --unsafe flag for convert_file."""
        with patch(
            'sys.argv',
            ['eml2pdf', 'convert_file', 'input.eml', 'output.pdf', '--unsafe'],
        ):
            args = get_args()
            self.assertTrue(args.unsafe)

    def test_convert_file_unsafe_default(self):
        """Test unsafe defaults to False for convert_file."""
        with patch(
            'sys.argv', ['eml2pdf', 'convert_file', 'input.eml', 'output.pdf']
        ):
            args = get_args()
            self.assertFalse(args.unsafe)

    def test_convert_file_verbose_flag(self):
        """Test -v/--verbose flag for convert_file."""
        with patch(
            'sys.argv',
            ['eml2pdf', 'convert_file', 'input.eml', 'output.pdf', '-v'],
        ):
            args = get_args()
            self.assertTrue(args.verbose)

        with patch(
            'sys.argv',
            [
                'eml2pdf',
                'convert_file',
                'input.eml',
                'output.pdf',
                '--verbose',
            ],
        ):
            args = get_args()
            self.assertTrue(args.verbose)

    def test_convert_file_verbose_default(self):
        """Test verbose defaults to False for convert_file."""
        with patch(
            'sys.argv', ['eml2pdf', 'convert_file', 'input.eml', 'output.pdf']
        ):
            args = get_args()
            self.assertFalse(args.verbose)

    def test_convert_file_quiet_flag(self):
        """Test -q/--quiet flag for convert_file."""
        with patch(
            'sys.argv',
            ['eml2pdf', 'convert_file', 'input.eml', 'output.pdf', '-q'],
        ):
            args = get_args()
            self.assertTrue(args.quiet)

        with patch(
            'sys.argv',
            ['eml2pdf', 'convert_file', 'input.eml', 'output.pdf', '--quiet'],
        ):
            args = get_args()
            self.assertTrue(args.quiet)

    def test_convert_file_quiet_default(self):
        """Test quiet defaults to False for convert_file."""
        with patch(
            'sys.argv', ['eml2pdf', 'convert_file', 'input.eml', 'output.pdf']
        ):
            args = get_args()
            self.assertFalse(args.quiet)

    def test_convert_file_combined_flags(self):
        """Test multiple flags can be combined for convert_file."""
        with patch(
            'sys.argv',
            [
                'eml2pdf',
                'convert_file',
                'input.eml',
                'output.pdf',
                '-d',
                '-v',
                '--unsafe',
                '-p',
                'letter',
            ],
        ):
            args = get_args()
            self.assertTrue(args.debug_html)
            self.assertTrue(args.verbose)
            self.assertTrue(args.unsafe)
            self.assertEqual(args.page, 'letter')
            self.assertFalse(args.quiet)


class TestMain(unittest.TestCase):
    """Test main() function.

    This just tests that main passes args correctly for some basic cases.
    """

    @patch('eml2pdf.eml2pdf.libeml2pdf.process_all_emls_in_dir')
    def test_main_convert_dir_basic(self, mock_process):
        """Test main() calls process_all_emls with correct arguments."""
        with patch('sys.argv', ['eml2pdf', 'convert_dir', 'input', 'output']):
            main()
            mock_process.assert_called_once()
            call_args = mock_process.call_args[0]
            self.assertEqual(call_args[0], Path('input'))
            self.assertEqual(call_args[1], Path('output'))

    @patch('eml2pdf.eml2pdf.libeml2pdf.process_eml')
    def test_main_convert_file_with_debug_html(self, mock_process):
        """Test main() passes debug_html flag correctly."""
        with patch(
            'sys.argv', ['eml2pdf', 'convert_file', 'input', 'output', '-d']
        ):
            main()
            call_args = mock_process.call_args[0]
            # debug_html is the 4th argument (index 3)
            self.assertTrue(call_args[3])


class TestLogLevelPropagation(unittest.TestCase):
    """Test that CLI log level settings propagate to libeml2pdf."""

    @patch('eml2pdf.eml2pdf.libeml2pdf.process_eml')
    def test_verbose_sets_debug_level(self, mock_process):
        """Test --verbose sets logger level to DEBUG."""
        import eml2pdf.libeml2pdf as lib

        orig_level = lib.logger.level
        with patch(
            'sys.argv',
            ['eml2pdf', 'convert_file', 'input.eml', 'output.pdf', '-v'],
        ):
            main()
            self.assertEqual(lib.logger.level, logging.DEBUG)
        lib.logger.setLevel(orig_level)

    @patch('eml2pdf.eml2pdf.libeml2pdf.process_eml')
    def test_quiet_sets_error_level(self, mock_process):
        """Test --quiet sets logger level to ERROR."""
        import eml2pdf.libeml2pdf as lib

        orig_level = lib.logger.level
        with patch(
            'sys.argv',
            ['eml2pdf', 'convert_file', 'input.eml', 'output.pdf', '-q'],
        ):
            main()
            self.assertEqual(lib.logger.level, logging.ERROR)
        lib.logger.setLevel(orig_level)

    @patch('eml2pdf.eml2pdf.libeml2pdf.process_eml')
    def test_default_sets_info_level(self, mock_process):
        """Test default (no flags) sets logger level to INFO."""
        import eml2pdf.libeml2pdf as lib

        orig_level = lib.logger.level
        with patch(
            'sys.argv', ['eml2pdf', 'convert_file', 'input.eml', 'output.pdf']
        ):
            main()
            self.assertEqual(lib.logger.level, logging.INFO)
        lib.logger.setLevel(orig_level)

    @patch('eml2pdf.eml2pdf.libeml2pdf.process_eml')
    def test_verbose_quiet_verbose_wins(self, mock_process):
        """Test --verbose and --quiet together, --verbose wins with warning."""
        import eml2pdf.libeml2pdf as lib

        orig_level = lib.logger.level
        with patch(
            'sys.argv',
            ['eml2pdf', 'convert_file', 'input.eml', 'output.pdf', '-v', '-q'],
        ):
            with patch('logging.warning') as mock_warning:
                main()
                mock_warning.assert_called_once()
                self.assertEqual(lib.logger.level, logging.DEBUG)
        lib.logger.setLevel(orig_level)
