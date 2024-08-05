"""Module for argument parsing and processing for the PDF to Markdown converter."""
import argparse
import os
import sys

from utils.configure_paths import get_config_settings


def parse_arguments():
    """Parse command-line arguments for the PDF to Markdown converter."""
    parser = argparse.ArgumentParser(description="Convert PDF files to Markdown.")
    parser.add_argument("--config", help="Path to the configuration file")
    parser.add_argument("pdf_dir", nargs="?", help="Directory containing PDF files")
    parser.add_argument("md_dir", nargs="?", help="Directory to save Markdown files")
    parser.add_argument(
        "converter",
        nargs="?",
        choices=["pdfminer", "markdownify"],
        default="pdfminer",
        help="Converter to use (default: pdfminer)",
    )
    parser.add_argument('--parallel', action='store_true', help='Enable parallel processing for downloading PDFs.')    
    parser.add_argument("--download_dir", help="Directory to save downloaded PDFs")
    parser.add_argument("--links_file", help="File containing links to process")
    return parser.parse_args()


def process_arguments(args):
    """Process parsed arguments and return configuration settings."""
    if args.config:
        pdf_directory, markdown_directory, converter_to_use = get_config_settings(
            args.config
        )
    else:
        pdf_directory = args.pdf_dir
        markdown_directory = args.md_dir
        converter_to_use = args.converter

    if not all([pdf_directory, markdown_directory, converter_to_use]):
        print("Error: Missing required arguments. Use --help for usage information.")
        sys.exit(1)

    os.makedirs(markdown_directory, exist_ok=True)

    return pdf_directory, markdown_directory, converter_to_use
