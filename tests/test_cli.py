"""Unit tests for CLI argument parsing and main function."""
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import logging
from eml2pdf.eml2pdf import get_args, main


class TestGetArgs(unittest.TestCase):
    """Test command-line argument parsing."""

    def test_basic_arguments(self):
        """Test parsing of required input_dir and output_dir arguments."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output']):
            args = get_args()
            self.assertEqual(args.input_dir, Path('input'))
            self.assertEqual(args.output_dir, Path('output'))

    def test_debug_html_flag(self):
        """Test -d/--debug_html flag."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output', '--debug_html']):
            args = get_args()
            self.assertTrue(args.debug_html)

        with patch('sys.argv', ['eml2pdf', 'input', 'output', '-d']):
            args = get_args()
            self.assertTrue(args.debug_html)

    def test_debug_html_default(self):
        """Test debug_html defaults to False."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output']):
            args = get_args()
            self.assertFalse(args.debug_html)

    def test_number_of_procs_flag(self):
        """Test -n/--number-of-procs flag."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output', '-n', '4']):
            args = get_args()
            self.assertEqual(args.number_of_procs, 4)

        with patch('sys.argv', ['eml2pdf', 'input', 'output', '--number-of-procs', '8']):
            args = get_args()
            self.assertEqual(args.number_of_procs, 8)

    def test_number_of_procs_default(self):
        """Test number_of_procs has a default value."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output']):
            args = get_args()
            # Should be set to CPU count, just verify it's a positive integer
            self.assertIsInstance(args.number_of_procs, int)
            self.assertGreater(args.number_of_procs, 0)

    def test_page_size_flag(self):
        """Test -p/--page flag."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output', '-p', 'letter']):
            args = get_args()
            self.assertEqual(args.page, 'letter')

        with patch('sys.argv', ['eml2pdf', 'input', 'output', '--page', 'a3']):
            args = get_args()
            self.assertEqual(args.page, 'a3')

        with patch('sys.argv', ['eml2pdf', 'input', 'output', '-p', 'a4 landscape']):
            args = get_args()
            self.assertEqual(args.page, 'a4 landscape')

    def test_page_size_default(self):
        """Test page size defaults to 'a4'."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output']):
            args = get_args()
            self.assertEqual(args.page, 'a4')

    def test_unsafe_flag(self):
        """Test --unsafe flag."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output', '--unsafe']):
            args = get_args()
            self.assertTrue(args.unsafe)

    def test_unsafe_default(self):
        """Test unsafe defaults to False."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output']):
            args = get_args()
            self.assertFalse(args.unsafe)

    def test_verbose_flag(self):
        """Test -v/--verbose flag."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output', '-v']):
            args = get_args()
            self.assertTrue(args.verbose)

        with patch('sys.argv', ['eml2pdf', 'input', 'output', '--verbose']):
            args = get_args()
            self.assertTrue(args.verbose)

    def test_verbose_default(self):
        """Test verbose defaults to False."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output']):
            args = get_args()
            self.assertFalse(args.verbose)

    def test_combined_flags(self):
        """Test multiple flags can be combined."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output', '-d', '-v', '--unsafe', '-n', '2', '-p', 'letter']):
            args = get_args()
            self.assertTrue(args.debug_html)
            self.assertTrue(args.verbose)
            self.assertTrue(args.unsafe)
            self.assertEqual(args.number_of_procs, 2)
            self.assertEqual(args.page, 'letter')


class TestMain(unittest.TestCase):
    """Test main() function."""

    @patch('eml2pdf.eml2pdf.libeml2pdf.process_all_emls')
    def test_main_basic(self, mock_process):
        """Test main() calls process_all_emls with correct arguments."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output']):
            main()
            mock_process.assert_called_once()
            call_args = mock_process.call_args[0]
            self.assertEqual(call_args[0], Path('input'))
            self.assertEqual(call_args[1], Path('output'))

    @patch('eml2pdf.eml2pdf.libeml2pdf.process_all_emls')
    def test_main_with_debug_html(self, mock_process):
        """Test main() passes debug_html flag correctly."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output', '-d']):
            main()
            call_args = mock_process.call_args[0]
            # debug_html is the 5th argument (index 4)
            self.assertTrue(call_args[4])

    @patch('eml2pdf.eml2pdf.libeml2pdf.process_all_emls')
    def test_main_with_number_of_procs(self, mock_process):
        """Test main() passes number_of_procs correctly."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output', '-n', '4']):
            main()
            call_args = mock_process.call_args[0]
            # number_of_procs is the 3rd argument (index 2)
            self.assertEqual(call_args[2], 4)

    @patch('eml2pdf.eml2pdf.libeml2pdf.process_all_emls')
    def test_main_with_page_size(self, mock_process):
        """Test main() passes page size correctly."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output', '-p', 'letter']):
            main()
            call_args = mock_process.call_args[0]
            # page is the 6th argument (index 5)
            self.assertEqual(call_args[5], 'letter')

    @patch('eml2pdf.eml2pdf.libeml2pdf.process_all_emls')
    def test_main_with_unsafe_flag(self, mock_process):
        """Test main() passes unsafe flag correctly."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output', '--unsafe']):
            main()
            call_args = mock_process.call_args[0]
            # unsafe is the 7th argument (index 6)
            self.assertTrue(call_args[6])

    @patch('eml2pdf.eml2pdf.libeml2pdf.process_all_emls')
    @patch('eml2pdf.eml2pdf.logger')
    def test_main_unsafe_warning(self, mock_logger, mock_process):
        """Test main() logs warning when --unsafe is used."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output', '--unsafe']):
            main()
            mock_logger.warning.assert_called_once()
            warning_message = mock_logger.warning.call_args[0][0]
            self.assertIn('sanitize', warning_message.lower())

    @patch('eml2pdf.eml2pdf.libeml2pdf.process_all_emls')
    @patch('eml2pdf.eml2pdf.logger')
    def test_main_no_warning_when_safe(self, mock_logger, mock_process):
        """Test main() doesn't log warning when --unsafe is not used."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output']):
            main()
            mock_logger.warning.assert_not_called()

    @patch('eml2pdf.eml2pdf.libeml2pdf.process_all_emls')
    @patch('eml2pdf.eml2pdf.logger')
    def test_main_verbose_sets_logging(self, mock_logger, mock_process):
        """Test main() sets logging level to DEBUG when verbose is enabled."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output', '-v']):
            main()
            mock_logger.setLevel.assert_called_once_with(logging.DEBUG)

    @patch('eml2pdf.eml2pdf.libeml2pdf.process_all_emls')
    @patch('eml2pdf.eml2pdf.logger')
    def test_main_no_verbose_no_logging_change(self, mock_logger, mock_process):
        """Test main() doesn't change logging level when verbose is not enabled."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output']):
            main()
            mock_logger.setLevel.assert_not_called()

    @patch('eml2pdf.eml2pdf.libeml2pdf.process_all_emls')
    def test_main_with_verbose_flag(self, mock_process):
        """Test main() passes verbose flag correctly."""
        with patch('sys.argv', ['eml2pdf', 'input', 'output', '-v']):
            main()
            call_args = mock_process.call_args[0]
            # verbose is the 4th argument (index 3)
            self.assertTrue(call_args[3])

    @patch('eml2pdf.eml2pdf.libeml2pdf.process_all_emls')
    def test_main_all_flags(self, mock_process):
        """Test main() with all flags enabled."""
        with patch('sys.argv', ['eml2pdf', 'in', 'out', '-d', '-v', '--unsafe', '-n', '8', '-p', 'a3']):
            main()
            call_args = mock_process.call_args[0]
            self.assertEqual(call_args[0], Path('in'))
            self.assertEqual(call_args[1], Path('out'))
            self.assertEqual(call_args[2], 8)  # number_of_procs
            self.assertTrue(call_args[3])  # verbose
            self.assertTrue(call_args[4])  # debug_html
            self.assertEqual(call_args[5], 'a3')  # page
            self.assertTrue(call_args[6])  # unsafe
