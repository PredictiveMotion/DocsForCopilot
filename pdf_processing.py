from markdown_formatting import format_text_as_markdown
from pdfminer.high_level import extract_text
import pdfplumber
from markdownify import markdownify as md

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