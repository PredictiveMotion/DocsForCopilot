from pdfminer.high_level import extract_text
from markdownify import markdownify as md

def pdf_to_markdown_markdownify(input_pdf_path):
    # Extract text from the PDF
    text = extract_text(input_pdf_path)

    # Convert the extracted text to Markdown
    markdown_text = md(text)
    return markdown_text
