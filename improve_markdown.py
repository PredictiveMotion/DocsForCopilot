import re
import sys
from markdown import markdown
from bs4 import BeautifulSoup

def improve_markdown(input_file, output_file):
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Convert Markdown to HTML
    html = markdown(content)

    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')

    # Initialize improved Markdown content
    improved_md = ""

    # Process headings
    for i in range(1, 7):
        for heading in soup.find_all(f'h{i}'):
            improved_md += f"{'#' * i} {heading.text.strip()}\n\n"

    # Process paragraphs
    for p in soup.find_all('p'):
        improved_md += f"{p.text.strip()}\n\n"

    # Process code blocks
    for pre in soup.find_all('pre'):
        code = pre.find('code')
        if code:
            language = code.get('class', [''])[0].replace('language-', '')
            improved_md += f"```{language}\n{code.text.strip()}\n```\n\n"

    # Process lists
    for ul in soup.find_all('ul'):
        for li in ul.find_all('li'):
            improved_md += f"- {li.text.strip()}\n"
        improved_md += "\n"

    for ol in soup.find_all('ol'):
        for i, li in enumerate(ol.find_all('li'), 1):
            improved_md += f"{i}. {li.text.strip()}\n"
        improved_md += "\n"

    # Process tables
    for table in soup.find_all('table'):
        headers = [th.text.strip() for th in table.find_all('th')]
        improved_md += "| " + " | ".join(headers) + " |\n"
        improved_md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        
        for row in table.find_all('tr')[1:]:
            cells = [td.text.strip() for td in row.find_all('td')]
            improved_md += "| " + " | ".join(cells) + " |\n"
        improved_md += "\n"

    # Remove extra newlines
    improved_md = re.sub(r'\n{3,}', '\n\n', improved_md)

    # Write the improved Markdown to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(improved_md)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python improve_markdown.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    improve_markdown(input_file, output_file)
    print(f"Improved Markdown has been written to {output_file}")