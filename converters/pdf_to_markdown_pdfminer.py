import pdfplumber
from collections import defaultdict

def extract_text_with_font_info(pdf_path):
    pages_content = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_content = []
            # Extract regular text
            for char in page.chars:
                page_content.append({
                    'type': 'text',
                    'text': char['text'],
                    'font_size': char['size'],
                    'top': char['top']
                })
            
            # Extract tables (potential code blocks)
            tables = page.find_tables()
            for table in tables:
                if len(table.rows) == 2 and len(table.cells[0]) == 1:  # Single-cell table with header
                    header = table.rows[0][0]
                    code = table.rows[1][0]
                    page_content.append({
                        'type': 'code_block',
                        'header': header,
                        'code': code,
                        'top': table.bbox[1]  # Use the top of the table as the position
                    })
            
            # Sort the page content by vertical position
            page_content.sort(key=lambda x: x['top'])
            pages_content.append(page_content)
    return pages_content

def determine_header_levels(pages_content):
    font_sizes = defaultdict(int)
    for page in pages_content:
        for element in page:
            if element['type'] == 'text':
                font_sizes[element['font_size']] += 1
    
    sorted_sizes = sorted(font_sizes.keys(), reverse=True)
    header_levels = {}
    for i, size in enumerate(sorted_sizes[:6]):  # Consider top 6 sizes as potential headers
        header_levels[size] = i + 1
    return header_levels

def convert_to_markdown(pages_content, header_levels):
    markdown_content = ""
    current_line = ""
    current_font_size = None
    for page in pages_content:
        prev_top = None
        for element in page:
            if element['type'] == 'text':
                text = element['text']
                font_size = element['font_size']
                top = element['top']

                if prev_top is not None and top - prev_top > 5:  # New line
                    if current_line:
                        markdown_content += process_line(current_line, current_font_size, header_levels)
                        current_line = ""
                        current_font_size = None

                current_line += text
                if current_font_size is None or font_size > current_font_size:
                    current_font_size = font_size

                prev_top = top
            elif element['type'] == 'code_block':
                if current_line:
                    markdown_content += process_line(current_line, current_font_size, header_levels)
                    current_line = ""
                    current_font_size = None
                markdown_content += process_code_block(element['header'], element['code'])

        # Process the last line of the page
        if current_line:
            markdown_content += process_line(current_line, current_font_size, header_levels)
            current_line = ""
            current_font_size = None

        markdown_content += "\n"  # Add a newline between pages

    return markdown_content

def process_line(line, font_size, header_levels):
    line = line.strip()
    if not line:
        return "\n"

    # Determine if it's a header
    if font_size in header_levels:
        level = header_levels[font_size]
        return f"{'#' * level} {line}\n\n"
    else:
        return f"{line}\n"

def process_code_block(header, code):
    return f"### {header}\n```\n{code}\n```\n\n"

def pdf_to_markdown_pdfminer(input_pdf_path):
    pages_content = extract_text_with_font_info(input_pdf_path)
    header_levels = determine_header_levels(pages_content)
    markdown_output = convert_to_markdown(pages_content, header_levels)
    return markdown_output

# The main execution part is left commented out as it's typically not included in module files
# pdf_path = "your_pdf_file.pdf"
# markdown_output = pdf_to_markdown_pdfminer(pdf_path)
# with open("output.md", "w", encoding="utf-8") as f:
#     f.write(markdown_output)
