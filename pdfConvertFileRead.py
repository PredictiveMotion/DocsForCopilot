import os
import sys
from pdfminer.high_level import extract_text

def simple_text_to_markdown(text):
    """
    Convert plain text to a simple Markdown format.
    """
    lines = text.split('\n')
    markdown_lines = []
    for line in lines:
        line = line.strip()
        if line:
            if line.isupper():
                markdown_lines.append(f"# {line}\n")
            else:
                markdown_lines.append(f"{line}\n")
        else:
            markdown_lines.append("\n")
    return "".join(markdown_lines)

def pdf_to_markdown(input_pdf_path, output_markdown_path):
    """
    Convert a PDF file to Markdown format.
    """
    try:
        # Extract text from the PDF
        text = extract_text(input_pdf_path)

        # Convert the extracted text to Markdown
        markdown = simple_text_to_markdown(text)

        # Save the Markdown to a file
        with open(output_markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        print(f"Markdown file created at: {output_markdown_path}")

    except Exception as e:
        print(f"An error occurred processing {input_pdf_path}: {e}")
        
        # Save the offending pdf's filename to a file
        with open("bad_pdfs.txt", "a") as f:
            f.write(f"{os.path.basename(input_pdf_path)}\n")
        
        # Delete the offending Markdown file if it exists
        if os.path.exists(output_markdown_path):
            os.remove(output_markdown_path)
            print(f"Deleted offending Markdown file: {output_markdown_path}")

def process_pdf_list(input_file, markdown_directory):
    """
    Process a list of PDF files from a text file and convert them to Markdown.
    """
    if not os.path.exists(markdown_directory):
        os.makedirs(markdown_directory)

    with open(input_file, 'r') as f:
        pdf_files = f.read().splitlines()

    for pdf_file in pdf_files:
        pdf_path = pdf_file.strip()
        if os.path.exists(pdf_path) and pdf_path.lower().endswith('.pdf'):
            markdown_filename = os.path.splitext(os.path.basename(pdf_path))[0] + '.md'
            markdown_path = os.path.join(markdown_directory, markdown_filename)
            pdf_to_markdown(pdf_path, markdown_path)
        else:
            print(f"Invalid or non-existent PDF file: {pdf_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python pdf_to_markdown.py <path_to_input_text_file> <path_to_markdown_directory>")
        sys.exit(1)

    input_file = sys.argv[1]
    markdown_directory = sys.argv[2]

    process_pdf_list(input_file, markdown_directory)