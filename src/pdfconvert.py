import os
import sys

# Ensure the parent directory of 'src' is in the sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from converters.pdf_to_markdown_pdfminer import pdf_to_markdown_pdfminer
from converters.pdf_to_markdown_markdownify import pdf_to_markdown_markdownify
from utils import parse_arguments, process_arguments

# Project root is already defined when setting up sys.path
PROJECT_ROOT = project_root

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
    pdf_directory, markdown_directory, converter_to_use = process_arguments(args)

    pdf_directory = os.path.abspath(pdf_directory)
    markdown_directory = os.path.abspath(markdown_directory)
    if not os.path.exists(pdf_directory):
        print(f"PDF directory does not exist: {pdf_directory}")
        sys.exit(1)

    if not os.path.exists(markdown_directory):
        os.makedirs(markdown_directory)
        print(f"Created Markdown directory: {markdown_directory}")

    pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith(".pdf")]
    total_files = len(pdf_files)

    for index, filename in enumerate(pdf_files, start=1):
        pdf_path = os.path.join(pdf_directory, filename)
        markdown_filename = os.path.splitext(filename)[0] + ".md"
        markdown_path = os.path.join(markdown_directory, markdown_filename)
        print(f"Processing file {index} of {total_files}: {filename}")
        pdf_to_markdown(pdf_path, markdown_path, converter_to_use)
        print(f"Completed file {index} of {total_files}: {filename}")

    print(f"All {total_files} PDF files have been processed.")

if __name__ == "__main__":
    main()
