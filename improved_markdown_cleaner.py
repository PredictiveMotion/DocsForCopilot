import re
import sys
import yaml
from markdown import markdown
from bs4 import BeautifulSoup
import os
from yaml.parser import ParserError
from markdown.extensions.fenced_code import FencedCodeExtension

def process_blockquotes(soup):
    blockquote_md = ""
    for blockquote in soup.find_all("blockquote"):
        blockquote_md += "> " + blockquote.text.strip().replace("\n", "\n> ") + "\n\n"
    return blockquote_md

def process_horizontal_rules(soup):
    hr_md = ""
    for hr in soup.find_all("hr"):
        hr_md += "---\n\n"
    return hr_md

def process_nested_lists(ul_or_ol, indent=""):
    list_md = ""
    for li in ul_or_ol.find_all("li", recursive=False):
        if ul_or_ol.name == "ul":
            list_md += f"{indent}- {li.contents[0].strip()}\n"
        else:
            list_md += f"{indent}1. {li.contents[0].strip()}\n"
        
        nested_ul = li.find("ul")
        nested_ol = li.find("ol")
        if nested_ul:
            list_md += process_nested_lists(nested_ul, indent + "  ")
        elif nested_ol:
            list_md += process_nested_lists(nested_ol, indent + "  ")
    return list_md

def improve_language_spec(language):
    language_map = {
        "js": "javascript",
        "py": "python",
        "rb": "ruby",
        "cs": "csharp",
        "cpp": "cpp",
        "ts": "typescript",
        # Add more mappings as needed
    }
    return language_map.get(language.lower(), language)

def improve_links(content):
    # Improve inline links
    content = re.sub(
        r"\[([^\]]+)\]\(([^\)]+)\)",
        lambda m: f"[{m.group(1).strip()}]({m.group(2).strip()})",
        content,
    )

    # Improve reference-style links
    content = re.sub(
        r"^\[([^\]]+)\]:\s*(.+)$",
        lambda m: f"[{m.group(1).strip()}]: {m.group(2).strip()}",
        content,
        flags=re.MULTILINE,
    )

    return content

def improve_images(content):
    # Improve inline images
    content = re.sub(
        r"!\[([^\]]*)\]\(([^\)]+)\)",
        lambda m: f"![{m.group(1).strip()}]({m.group(2).strip()})",
        content,
    )

    return content

def remove_repetitive_text(content):
    patterns_to_remove = [
        r"６ Collaborate with us on\s*GitHub\s*The source for this content can\s*be found on GitHub, where you\s*can also create and review\s*issues and pull requests\. For\s*more information, see our\s*contributor guide\.",
        r"\.NET feedback\s*\.NET is an open source project\.\s*Select a link to provide feedback:\s*Open a documentation issue\s*Provide product feedback",
        r"\\.NET feedback\\s*\\.NET is an open source project\\.\\s*Select a link to provide feedback:\\s*Open a documentation issue\\s*Provide product feedback"
        r".NET feedback",
        r".NET is an open source project.",
        r"Select a link to provide feedback:",
        r"Open a documentation issue",
        r"Provide product feedback",
        r"Feedback",
        r"Collaborate with us on GitHub",
        r"The source for this content can be found on GitHub, where you can also create and review issues and pull requests. For more information, see our contributor guide.",
        r".NET feedback",
        r"For more information about Accessibility, see the Microsoft Active Accessibility",
        r"Remarks",
        r"６ Collaborate with us on",
        r"Collaborate with us on",
        r"GitHub",
    ]

    for pattern in patterns_to_remove:
        content = re.sub(pattern, "", content, flags=re.DOTALL | re.MULTILINE)

    return content

def extract_frontmatter(content):
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if frontmatter_match:
        frontmatter_str = frontmatter_match.group(1)
        try:
            frontmatter = yaml.safe_load(frontmatter_str)
            content = content[frontmatter_match.end():]
            return frontmatter, content
        except ParserError as e:
            print(f"Warning: Error parsing YAML frontmatter: {str(e)}")
        except Exception as e:
            print(f"Warning: Unexpected error processing frontmatter: {str(e)}")
    return None, content

def improve_markdown(input_file, output_file):
    try:
        # Read the input file
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract and process YAML frontmatter
        frontmatter, content = extract_frontmatter(content)

        # Convert Markdown to HTML
        html = markdown(content, extensions=[FencedCodeExtension(), "tables"])

        # Parse the HTML
        soup = BeautifulSoup(html, "html.parser")

        # Initialize improved Markdown content
        improved_md = ""

        # Add processed frontmatter
        if frontmatter:
            improved_md += f"---\n{yaml.dump(frontmatter, sort_keys=False)}---\n\n"

        # Process headings
        for i in range(1, 7):
            for heading in soup.find_all(f"h{i}"):
                improved_md += f"{'#' * i} {heading.text.strip()}\n\n"

        # Process paragraphs
        for p in soup.find_all("p"):
            paragraph_content = p.decode_contents()
            # Convert <strong> to **
            paragraph_content = re.sub(r'<strong>(.*?)</strong>', r'**\1**', paragraph_content)
            # Convert <em> to *
            paragraph_content = re.sub(r'<em>(.*?)</em>', r'*\1*', paragraph_content)
            # Convert <a> to []()
            paragraph_content = re.sub(r'<a href="(.*?)">(.*?)</a>', r'[\2](\1)', paragraph_content)
            improved_md += f"{paragraph_content.strip()}\n\n"

        # Process code blocks
        for pre in soup.find_all("pre"):
            code = pre.find("code")
            if code:
                language = code.get("class", [""])[0].replace("language-", "")
                language = improve_language_spec(language)
                improved_md += f"```{language}\n{code.text.strip()}\n```\n\n"

        # Process lists
        for ul in soup.find_all("ul", recursive=False):
            improved_md += process_nested_lists(ul)
            improved_md += "\n"

        for ol in soup.find_all("ol", recursive=False):
            improved_md += process_nested_lists(ol)
            improved_md += "\n"

        # Process tables
        for table in soup.find_all("table"):
            headers = [th.text.strip() for th in table.find_all("th")]
            improved_md += "| " + " | ".join(headers) + " |\n"
            improved_md += "| " + " | ".join(["---"] * len(headers)) + " |\n"

            for row in table.find_all("tr")[1:]:
                cells = [td.text.strip() for td in row.find_all("td")]
                improved_md += "| " + " | ".join(cells) + " |\n"
            improved_md += "\n"

        # Process blockquotes
        improved_md += process_blockquotes(soup)

        # Process horizontal rules
        improved_md += process_horizontal_rules(soup)

        # Improve link formatting
        improved_md = improve_links(improved_md)

        # Improve image references
        improved_md = improve_images(improved_md)

        # Remove extra newlines
        improved_md = re.sub(r"\n{3,}", "\n\n", improved_md)

        # Remove repetitive text
        improved_md = remove_repetitive_text(improved_md)

        # Write the improved Markdown to the output file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(improved_md)

    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
    except PermissionError:
        print(f"Error: Permission denied when accessing '{input_file}' or '{output_file}'.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python improved_markdown_cleaner.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        sys.exit(1)

    try:
        improve_markdown(input_file, output_file)
        print(f"Improved Markdown has been written to {output_file}")
    except Exception as e:
        print(f"An error occurred while processing the file: {str(e)}")
        sys.exit(1)
