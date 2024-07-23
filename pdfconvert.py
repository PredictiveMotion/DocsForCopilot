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
import argparse
import pdfplumber
from pdfminer.high_level import extract_text
from markdownify import markdownify as md
from config_management import read_config
from markdown_formatting import format_text_as_markdown



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



def parse_arguments():
    """
    Parse the command line arguments.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
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





def configure_paths_and_converter(args):
    """
    Configures the paths and converter to use based on the provided arguments.

    Args:
        args (argparse.Namespace): The command-line arguments.

    Returns:
        tuple: A tuple containing the PDF directory, Markdown directory, and converter to use.
    """
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
    return pdf_directory, markdown_directory, converter_to_use



def parse_arguments_and_configure_paths():
    """
    Parses the command line arguments and configures the paths for PDF directory, markdown directory, and converter to use.

    Returns:
        pdf_directory (str): The path to the PDF directory.
        markdown_directory (str): The path to the markdown directory.
        converter_to_use (str): The converter to use for the conversion process.
    """
    args = parse_arguments()
    pdf_directory, markdown_directory, converter_to_use = configure_paths_and_converter(args)
    return pdf_directory, markdown_directory, converter_to_use



def create_directory(directory):
    os.makedirs(directory, exist_ok=True)




def main():
    """
    Converts PDF files to Markdown using the specified converter.

    This function takes the PDF directory, Markdown directory, and converter to use as input.
    It creates the Markdown directory if it doesn't exist, then iterates over the PDF files in the PDF directory.
    For each PDF file, it generates the corresponding Markdown filename and path.
    Finally, it calls the `pdf_to_markdown` function to convert the PDF to Markdown using the specified converter.

    Args:
        None

    Returns:
        None
    """
    pdf_directory, markdown_directory, converter_to_use = parse_arguments_and_configure_paths()
    create_directory(markdown_directory)

    for filename in os.listdir(pdf_directory):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_directory, filename)
            markdown_filename = os.path.splitext(filename)[0] + ".md"
            markdown_path = os.path.join(markdown_directory, markdown_filename)
            pdf_to_markdown(pdf_path, markdown_path, converter_to_use)




if __name__ == "__main__":
    main()
