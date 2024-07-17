"""
pdfConvert3_using_pdfminer.py

This script converts PDF files to Markdown format. It uses the pdfplumber library to extract 
text from the PDF files, and then saves the extracted text as Markdown files. 

The script also handles errors during the conversion process, logging any files that could not 
be converted and deleting any partially converted Markdown files.

Usage: python pdf_to_markdown.py <path_to_pdf_directory> <path_to_markdown_directory>
"""

import os
import sys
import pdfplumber


def pdf_to_markdown(input_pdf_path, output_markdown_path):
    """
    Convert a PDF file to Markdown format.

    Args:
        input_pdf_path (str): The path to the PDF file.
        output_markdown_path (str): The path to save the Markdown file.

    Raises:
        Exception: If an error occurs during the conversion process.

    Returns:
        None
    """
    try:
        # Extract text from the PDF using pdfplumber
        markdown_text = ""
        with pdfplumber.open(input_pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    markdown_text += text + "\n\n"

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


if __name__ == "__main__":
    if len(sys.argv) != 3:
        ERROR_MSG = ("Usage: python pdf_to_markdown.py "
             "<path_to_pdf_directory> "
             "<path_to_markdown_directory>")
        print(ERROR_MSG)
        sys.exit(1)

    pdf_directory = sys.argv[1]
    markdown_directory = sys.argv[2]

    if not os.path.exists(markdown_directory):
        os.makedirs(markdown_directory)

    for filename in os.listdir(pdf_directory):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_directory, filename)
            markdown_filename = os.path.splitext(filename)[0] + ".md"
            markdown_path = os.path.join(markdown_directory, markdown_filename)
            pdf_to_markdown(pdf_path, markdown_path)
