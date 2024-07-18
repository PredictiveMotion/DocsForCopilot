"""
pdfConvert3_using_pdfminer.py

This script converts PDF files to Markdown format. It uses the pdfplumber library to extract 
text from the PDF files, and then saves the extracted text as Markdown files. 

The script also handles errors during the conversion process, logging any files that could not 
be converted and deleting any partially converted Markdown files.

Usage: python pdf_to_markdown.py <pdf_dir> <md_dir> <converter>"
"""

import os
import sys
import pdfplumber
from pdfminer.high_level import extract_text
from markdownify import markdownify as md
import configparser
import argparse


def format_text_as_markdown(text):
    """
    Format raw text into a basic Markdown structure.

    Args:
        text (str): The raw text extracted from the PDF.

    Returns:
        str: The formatted Markdown text.
    """
    lines = text.split("\n")
    markdown_lines = []

    for line in lines:
        stripped_line = line.strip()

        # Heading formatting: Simple heuristic for identifying headings
        if stripped_line.isupper() and len(stripped_line.split()) < 10:
            markdown_lines.append(f"## {stripped_line}")
        # Bullet points: Simple heuristic for lists
        elif stripped_line.startswith("- ") or stripped_line.startswith("* "):
            markdown_lines.append(f"{stripped_line}")
        # Regular paragraph
        elif stripped_line:
            markdown_lines.append(f"{stripped_line}")

    return "\n\n".join(markdown_lines)


def pdf_to_markdown_pdfminer(input_pdf_path):
    """
    Convert a PDF file to Markdown format using pdfplumber.

    Args:
        input_pdf_path (str): The path to the PDF file.

    Returns:
        str: The markdown text.
    """
    markdown_text = ""
    with pdfplumber.open(input_pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                markdown_text += format_text_as_markdown(text) + "\n\n"
    return markdown_text


def pdf_to_markdown_markdownify(input_pdf_path):
    """
    Convert a PDF file to Markdown format using markdownify.

    Args:
        input_pdf_path (str): The path to the PDF file.

    Returns:
        str: The markdown text.
    """
    # Extract text from the PDF
    text = extract_text(input_pdf_path)

    # Convert the extracted text to Markdown
    markdown_text = md(text)
    return markdown_text


def pdf_to_markdown(input_pdf_path, output_markdown_path, converter="pdfminer"):
    """
    Convert a PDF file to Markdown format.

    Args:
        input_pdf_path (str): The path to the PDF file.
        output_markdown_path (str): The path to save the Markdown file.
        converter (str, optional): The converter to use. Defaults to 'pdfminer'.

    Raises:
        Exception: If an error occurs during the conversion process.

    Returns:
        None
    """
    try:
        if converter == "markdownify":
            markdown_text = pdf_to_markdown_markdownify(input_pdf_path)
        elif converter == "pdfminer":
            markdown_text = pdf_to_markdown_pdfminer(input_pdf_path)
        else:
            print(f"Invalid converter: {converter}")
            sys.exit(1)

        # Save the Markdown to a file
        with open(output_markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        print(f"Markdown file created at: {output_markdown_path}")

    except IOError as e:
        print(f"An error occurred: {e}")
        # Save the offending pdf's filename to a file
        with open("bad_pdfs.txt", "a", encoding="utf-8") as f:
            bad_pdf = os.path.basename(input_pdf_path)
            f.write(f"{bad_pdf}\n")
        # Delete the offending Markdown file if it exists
        if os.path.exists(output_markdown_path):
            os.remove(output_markdown_path)
            print(f"Deleted offending Markdown file: {output_markdown_path}")


def read_config(config_file="config.ini"):
    config = configparser.ConfigParser()
    config.read(config_file)
    return config


def main():
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

    args = parser.parse_args()

    if args.config:
        config = read_config(args.config)
        pdf_directory = config["PDFSettings"]["input_folder"]
        markdown_directory = config["PDFSettings"]["output_folder"]
        converter_to_use = config["PDFSettings"]["converter"]
    else:
        if not args.pdf_dir or not args.md_dir:
            print(
                "Usage: python pdf_to_markdown.py <pdf_dir> <md_dir> [converter] OR --config <config.ini>"
            )
            sys.exit(1)

        pdf_directory = args.pdf_dir
        markdown_directory = args.md_dir
        converter_to_use = args.converter

    if not os.path.exists(markdown_directory):
        os.makedirs(markdown_directory)

    for filename in os.listdir(pdf_directory):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_directory, filename)
            markdown_filename = os.path.splitext(filename)[0] + ".md"
            markdown_path = os.path.join(markdown_directory, markdown_filename)
            pdf_to_markdown(pdf_path, markdown_path, converter_to_use)


if __name__ == "__main__":
    main()
