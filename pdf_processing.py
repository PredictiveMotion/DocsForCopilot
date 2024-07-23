from markdown_formatting import format_text_as_markdown
from pdfminer.high_level import extract_text
import pdfplumber
from markdownify import markdownify as md


def pdf_to_markdown_pdfminer(input_pdf_path):
    markdown_text = ""
    with pdfplumber.open(input_pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                markdown_text += format_text_as_markdown(text) + "\n\n"
    return markdown_text


def pdf_to_markdown_markdownify(input_pdf_path):
    text = extract_text(input_pdf_path)
    markdown_text = md(text)
    return markdown_text
