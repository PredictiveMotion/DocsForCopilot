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
        print(f"An error occurred: {e}")
        
        # Save the offending pdf's filename to a file
        with open("bad_pdfs.txt", "a") as f:
            f.write(f"{os.path.basename(input_pdf_path)}\n")
        
        # Delete the offending Markdown file if it exists
        if os.path.exists(output_markdown_path):
            os.remove(output_markdown_path)
            print(f"Deleted offending Markdown file: {output_markdown_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python pdf_to_markdown.py <path_to_pdf_directory> <path_to_markdown_directory>")
        sys.exit(1)

    pdf_directory = sys.argv[1]
    markdown_directory = sys.argv[2]

    if not os.path.exists(markdown_directory):
        os.makedirs(markdown_directory)

    for filename in os.listdir(pdf_directory):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_directory, filename)
            markdown_filename = os.path.splitext(filename)[0] + '.md'
            markdown_path = os.path.join(markdown_directory, markdown_filename)
            pdf_to_markdown(pdf_path, markdown_path)