import argparse

import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="Convert PDF files to Markdown.")
    parser.add_argument("--config", help="Path to the configuration file")
    parser.add_argument("--pdf_dir", help="Directory containing PDF files")
    parser.add_argument("--md_dir", help="Directory to save Markdown files")
    parser.add_argument("--converter", choices=["pdfminer", "markdownify"], default="pdfminer",
                        help="Converter to use (default: pdfminer)")
    
    return parser.parse_args()
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to the configuration file.")
    parser.add_argument("pdf_dir", nargs="?", help="Path to the PDF directory.")
    parser.add_argument("md_dir", nargs="?", help="Path to the Markdown directory.")
    parser.add_argument(
        "converter",
        nargs="?",
        default="pdfminer",
        help="The converter to use: 'pdfminer' or 'markdownify'. Defaults to 'pdfminer'.",
    )

    return parser.parse_args()
