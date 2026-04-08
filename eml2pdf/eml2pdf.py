import argparse
import logging
import os
from pathlib import Path
import sys

from . import libeml2pdf

logging.basicConfig()
logger = logging.getLogger(__name__)
libeml2pdf_logger = logging.getLogger('eml2pdf.libeml2pdf')

loggers = [logger, libeml2pdf_logger]


def get_args() -> argparse.Namespace:
    """Construct arguments for CLI script."""

    # Determine default number of processors (cross-platform)
    if hasattr(os, 'sched_getaffinity'):
        default_procs = len(os.sched_getaffinity(0))
    else:
        default_procs = os.cpu_count() or 1

    parser = argparse.ArgumentParser(description="Convert EML files to PDF")

    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("-p", "--page", metavar="size", default='a4',
                        help="One of a3, a4, a5, b4, b5, letter, legal, or "
                        "ledger, with or without \"landscape\", for example: "
                        "\"a4 landscape\" or a3. Surround with quotes if "
                        "there is a space in the argument value. "
                        "Defaults to \"a4\", implying portrait.")
    parent_parser.add_argument("--unsafe", action="store_true", default=False,
                        help="Don't sanitize HTML from potentially unsafe "
                        "elements such as remote images, scripts, etc. This "
                        "may expose sensitive user information.")
    parent_parser.add_argument("-d", "--debug_html", action="store_true",
                        help="Write intermediate html file next to PDF's")
    parent_parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show a lot of verbose debugging info. Forces '
                        'number of procs to 1.')
    parent_parser.add_argument('-q', '--quiet', action='store_true',
                        help='Show only errors.')


    subparsers = parser.add_subparsers(required=True,
                                       title='supported subcommands:',
                                       help='Use {subcommand} --help for '
                                       'options.')

    convert_dir = subparsers.add_parser('convert_dir',
                                        parents = [parent_parser],
                                        help='Convert all EML '
                                        'files in an input dir to PDF files '
                                        'in an output dir.')
    convert_dir.add_argument("input_dir", type=Path,
                        help="Directory containing EML files")
    convert_dir.add_argument("output_dir", type=Path,
                        help="Directory for PDF output")
    convert_dir.add_argument("-n", "--number-of-procs", metavar='number',
                             type=int, default=default_procs, help='Number of '
                             'parallel processes. Defaults to the number of '
                             'available logical CPU\'s to eml_to_pdf.')

    convert_file = subparsers.add_parser('convert_file',
                                         parents = [parent_parser],
                                         help='Convert a single EML file to a '
                                         'single PDF')
    convert_file.add_argument('input_file', type=Path, help='Input EML file '
                              'to convert')
    convert_file.add_argument('output_file', type=Path, help='Output PDF file '
                              'to convert to')

    args = parser.parse_args()
    return args


def main():
    # Set up argument parser
    args = get_args()
    if args.unsafe:
        logger.warning('WARNING! Not trying to '
                       'sanitize HTML. This may expose sensitive user '
                       'information.')

    if args.verbose:
        new_log_level = logging.DEBUG
        if args.quiet:
            logging.warning('Overriding --quiet with --verbose.')
    elif args.quiet:
        new_log_level = logging.ERROR
    else: # verbose and quiet both false = normal output
        new_log_level = logging.INFO

    for l in loggers: l.setLevel(new_log_level)
    logger.debug(f'Registered loggers: {logging.root.manager.loggerDict}')

    if 'input_file' in args:
        libeml2pdf.process_eml(args.input_file, args.output_file, args.page,
                               args.debug_html, args.unsafe)
    elif 'input_dir' in args:
        libeml2pdf.process_all_emls_in_dir(args.input_dir, args.output_dir,
                                           args.number_of_procs,
                                           args.debug_html, args.page,
                                           args.unsafe)
    else:
        raise ValueError(f'Could not process arguments: {sys.argv}')


if __name__ == "__main__":
    main()
