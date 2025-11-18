import argparse
from pathlib import Path
import os
import logging
from . import libeml2pdf

logging.basicConfig()
logger = logging.getLogger(__name__)


def get_args() -> argparse.Namespace:
    """Construct arguments for CLI script."""

    # Determine default number of processors (cross-platform)
    if hasattr(os, 'sched_getaffinity'):
        default_procs = len(os.sched_getaffinity(0))
    else:
        default_procs = os.cpu_count() or 1

    parser = argparse.ArgumentParser(description="Convert EML files to PDF")
    parser.add_argument("input_dir", type=Path,
                        help="Directory containing EML files")
    parser.add_argument("output_dir", type=Path,
                        help="Directory for PDF output")
    parser.add_argument("-d", "--debug_html", action="store_true",
                        help="Write intermediate html file next to pdf's")
    parser.add_argument("-n", "--number-of-procs", metavar='number', type=int,
                        default=default_procs,
                        help="Number of parallel processes. Defaults to "
                        "the number of available logical CPU's to eml_to_pdf.")
    parser.add_argument("-p", "--page", metavar="size", default='a4',
                        help="a3 a4 a5 b4 b5 letter legal or ledger with "
                        "or without 'landscape', for example: 'a4 landscape' "
                        "or 'a3' including quotes. Defaults to 'a4', implying "
                        "portrait.")
    parser.add_argument("--unsafe", action="store_true", default=False,
                        help="Don't sanitize HTML from potentially unsafe "
                        "elements such as remote images, scripts, etc. This "
                        "may expose sensitive user information.")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show a lot of verbose debugging info. Forces '
                        'number of procs to 1.')
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
        logger.setLevel(logging.DEBUG)

    libeml2pdf.process_all_emls(args.input_dir, args.output_dir,
                                args.number_of_procs, args.verbose,
                                args.debug_html, args.page, args.unsafe)


if __name__ == "__main__":
    main()
