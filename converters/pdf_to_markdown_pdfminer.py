import pdfplumber
from markdown_formatting import format_text_as_markdown

def pdf_to_markdown_pdfminer(input_pdf_path):
    markdown_text = ""
    with pdfplumber.open(input_pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                markdown_text += format_text_as_markdown(text) + "\n\n"
    return markdown_text
