import pdfplumber
#from markdown_formatting import format_text_as_markdown



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
    markdown_text = ""
    with pdfplumber.open(input_pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                markdown_text += format_text_as_markdown(text) + "\n\n"
    return markdown_text
