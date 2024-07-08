import sys
from pdfminer.high_level import extract_text
from markdownify import markdownify as md


def pdf_to_markdown(input_pdf_path, output_markdown_path):
    """
    Convert a PDF file to Markdown format.

    Args:
        pdf_path (str): The path to the PDF file.
        markdown_path (str): The path to save the Markdown file.

    Raises:
        Exception: If an error occurs during the conversion process.

    Returns:
        None
    """
    try:
        # Extract text from the PDF
        text = extract_text(input_pdf_path)

        # Convert the extracted text to Markdown
        markdown = md(text)

        # Save the Markdown to a file
        with open(output_markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        print(f"Markdown file created at: {output_markdown_path}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python pdf_to_markdown.py <path_to_pdf> <path_to_markdown>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    markdown_path = sys.argv[2]

    pdf_to_markdown(pdf_path, markdown_path)
