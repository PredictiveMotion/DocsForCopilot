import argparse

def parse_arguments():
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
