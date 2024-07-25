import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description="Convert PDF files to Markdown.")
    parser.add_argument("--config", help="Path to the configuration file")
    parser.add_argument("pdf_dir", nargs="?", help="Directory containing PDF files")
    parser.add_argument("md_dir", nargs="?", help="Directory to save Markdown files")
    parser.add_argument("converter", nargs="?", choices=["pdfminer", "markdownify"], default="pdfminer",
                        help="Converter to use (default: pdfminer)")
    return parser.parse_args()
