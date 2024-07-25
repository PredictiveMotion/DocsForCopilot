import os
import sys
import argparse

from converters.pdf_to_markdown_pdfminer import pdf_to_markdown_pdfminer
from converters.pdf_to_markdown_markdownify import pdf_to_markdown_markdownify
from utils.configure_paths import get_config_settings

def parse_arguments():
    parser = argparse.ArgumentParser(description="Convert PDF files to Markdown.")
    parser.add_argument("--config", help="Path to the configuration file")
    parser.add_argument("pdf_dir", nargs="?", help="Directory containing PDF files")
    parser.add_argument("md_dir", nargs="?", help="Directory to save Markdown files")
    parser.add_argument("converter", nargs="?", choices=["pdfminer", "markdownify"], default="pdfminer",
                        help="Converter to use (default: pdfminer)")
    return parser.parse_args()

def pdf_to_markdown(input_pdf_path, output_markdown_path, converter="pdfminer"):
    try:
        if converter == "markdownify":
            markdown_text = pdf_to_markdown_markdownify(input_pdf_path)
        elif converter == "pdfminer":
            markdown_text = pdf_to_markdown_pdfminer(input_pdf_path)
        else:
            print(f"Invalid converter: {converter}")
            sys.exit(1)
        with open(output_markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        print(f"Markdown file created at: {output_markdown_path}")

    except IOError as e:
        print(f"An error occurred: {e}")
        with open("bad_pdfs.txt", "a", encoding="utf-8") as f:
            bad_pdf = os.path.basename(input_pdf_path)
            f.write(f"{bad_pdf}\n")
        if os.path.exists(output_markdown_path):
            os.remove(output_markdown_path)
            print(f"Deleted offending Markdown file: {output_markdown_path}")




def main():
    args = parse_arguments()
    
    if args.config:
        pdf_directory, markdown_directory, converter_to_use = get_config_settings(args.config)
    else:
        pdf_directory = args.pdf_dir
        markdown_directory = args.md_dir
        converter_to_use = args.converter

    if not all([pdf_directory, markdown_directory, converter_to_use]):
        print("Error: Missing required arguments. Use --help for usage information.")
        sys.exit(1)

    os.makedirs(markdown_directory, exist_ok=True)

    for filename in os.listdir(pdf_directory):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_directory, filename)
            markdown_filename = os.path.splitext(filename)[0] + ".md"
            markdown_path = os.path.join(markdown_directory, markdown_filename)
            pdf_to_markdown(pdf_path, markdown_path, converter_to_use)

if __name__ == "__main__":
    main()
