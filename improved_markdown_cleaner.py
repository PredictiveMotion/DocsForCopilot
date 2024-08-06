import re
import sys
import yaml
import argparse
import logging
from markdown import markdown
from bs4 import BeautifulSoup
import os
from yaml.parser import ParserError
from markdown.extensions.fenced_code import FencedCodeExtension

def log_markdown_change(change_type, details):
    logging.info(f"improve_markdown2:{change_type}:{details}")

def load_config(config_file):
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logging.error(f"Error loading configuration file: {str(e)}")
        return {}

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

def remove_repetitive_text(content, patterns_to_remove):
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

def improve_markdown2(input_file, output_file, config):
    logging.info(f"Starting second improvement pass for {input_file}")
    
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()
    logging.debug(f"Read {len(content)} characters from {input_file}")

    frontmatter, content = extract_frontmatter(content)
    if frontmatter:
        logging.debug("Extracted frontmatter")

    html = markdown(content, extensions=["fenced_code", "tables"])
    logging.debug("Converted Markdown to HTML")

    soup = BeautifulSoup(html, "html.parser")
    logging.debug("Parsed HTML with BeautifulSoup")

    improved_md = ""

    if frontmatter:
        improved_md += "---\n" + yaml.dump(frontmatter) + "---\n\n"

    heading_stack = []
    for tag in soup.children:
        if isinstance(tag, str):
            improved_md += tag.strip() + "\n\n"
            continue
        
        if tag.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(tag.name[1])
            text = tag.get_text(strip=True)
            
            while heading_stack and level <= heading_stack[-1]:
                heading_stack.pop()
            
            if not heading_stack or level > heading_stack[-1]:
                heading_stack.append(level)
            
            new_level = len(heading_stack)
            improved_md += f"{'#' * new_level} {text}\n\n"
            log_markdown_change('header_level_changed', f"'{text}' from H{level} to H{new_level}")
        
        elif tag.name == "p":
            improved_md += tag.get_text(strip=True) + "\n\n"
        
        elif tag.name == "pre":
            code = tag.get_text(strip=True)
            language = tag.get('class', [None])[0]
            if language:
                language = improve_language_spec(language)
                improved_md += f"```{language}\n{code}\n```\n\n"
            else:
                improved_md += f"```\n{code}\n```\n\n"
        
        elif tag.name == "ul":
            improved_md += process_nested_lists(tag)
        
        elif tag.name == "ol":
            improved_md += process_nested_lists(tag)
        
        elif tag.name == "table":
            improved_md += process_tables(tag)
        
        elif tag.name == "blockquote":
            improved_md += "> " + tag.get_text(strip=True).replace("\n", "\n> ") + "\n\n"
        
        elif tag.name == "hr":
            improved_md += "---\n\n"

    improved_md = improve_links(improved_md)
    logging.debug("Improved link formatting")

    improved_md = improve_images(improved_md)
    logging.debug("Improved image references")

    improved_md = re.sub(r"\n{3,}", "\n\n", improved_md)
    logging.debug("Removed extra newlines")

    improved_md = remove_repetitive_text(improved_md, config.get('patterns_to_remove', []))
    logging.debug("Removed repetitive text")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(improved_md)
    logging.info(f"Wrote improved Markdown to {output_file}")


def improve_markdown(input_file, output_file, config):
    try:
        logging.info(f"Starting improvement process for {input_file}")
        
        # Read the input file
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()
        logging.debug(f"Read {len(content)} characters from {input_file}")

        # Extract and process YAML frontmatter
        frontmatter, content = extract_frontmatter(content)
        if frontmatter:
            logging.debug("Extracted YAML frontmatter")

        # Convert Markdown to HTML
        html = markdown(content, extensions=[FencedCodeExtension(), "tables"])
        logging.debug("Converted Markdown to HTML")

        # Parse the HTML
        soup = BeautifulSoup(html, "html.parser")
        logging.debug("Parsed HTML with BeautifulSoup")

        # Initialize improved Markdown content
        improved_md = ""

        # Add processed frontmatter
        if frontmatter:
            improved_md += f"---\n{yaml.dump(frontmatter, sort_keys=False)}---\n\n"
            logging.debug("Added processed frontmatter to improved Markdown")

        heading_stack = []
        for tag in soup.children:
            if isinstance(tag, str):
                improved_md += tag.strip() + "\n\n"
                continue
            
            if tag.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                level = int(tag.name[1])
                text = tag.get_text(strip=True)
                
                while heading_stack and level <= heading_stack[-1]:
                    heading_stack.pop()
                
                if not heading_stack or level > heading_stack[-1]:
                    heading_stack.append(level)
                
                new_level = len(heading_stack)
                improved_md += f"{'#' * new_level} {text}\n\n"
            
            elif tag.name == "p":
                paragraph_content = tag.decode_contents()
                # Convert <strong> to **
                paragraph_content = re.sub(r'<strong>(.*?)</strong>', r'**\1**', paragraph_content)
                # Convert <em> to *
                paragraph_content = re.sub(r'<em>(.*?)</em>', r'*\1*', paragraph_content)
                # Convert <a> to []()
                paragraph_content = re.sub(r'<a href="(.*?)">(.*?)</a>', r'[\2](\1)', paragraph_content)
                improved_md += f"{paragraph_content.strip()}\n\n"
            
            elif tag.name == "pre":
                code = tag.find("code")
                if code:
                    language = code.get("class", [""])[0].replace("language-", "")
                    language = improve_language_spec(language, config.get('language_mapping', {}))
                    improved_md += f"```{language}\n{code.text.strip()}\n```\n\n"
            
            elif tag.name == "ul":
                improved_md += process_nested_lists(tag)
                improved_md += "\n"
            
            elif tag.name == "ol":
                improved_md += process_nested_lists(tag)
                improved_md += "\n"
            
            elif tag.name == "table":
                headers = [th.text.strip() for th in tag.find_all("th")]
                improved_md += "| " + " | ".join(headers) + " |\n"
                improved_md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
                for row in tag.find_all("tr")[1:]:
                    cells = [td.text.strip() for td in row.find_all("td")]
                    improved_md += "| " + " | ".join(cells) + " |\n"
                improved_md += "\n"
            
            elif tag.name == "blockquote":
                improved_md += "> " + tag.get_text(strip=True).replace("\n", "\n> ") + "\n\n"
            
            elif tag.name == "hr":
                improved_md += "---\n\n"

        # Improve link formatting
        improved_md = improve_links(improved_md)
        logging.debug("Improved link formatting")

        # Improve image references
        improved_md = improve_images(improved_md)
        logging.debug("Improved image references")

        # Remove extra newlines
        improved_md = re.sub(r"\n{3,}", "\n\n", improved_md)
        logging.debug("Removed extra newlines")

        # Remove repetitive text
        improved_md = remove_repetitive_text(improved_md, config.get('patterns_to_remove', []))
        logging.debug("Removed repetitive text")

        # Write the improved Markdown to the output file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(improved_md)
        logging.info(f"Wrote improved Markdown to {output_file}")

    except FileNotFoundError:
        logging.error(f"Input file '{input_file}' not found.")
        sys.exit(1)
    except PermissionError:
        logging.error(f"Permission denied when accessing '{input_file}' or '{output_file}'.")
        sys.exit(1)
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)

def parse_arguments():
    parser = argparse.ArgumentParser(description="Improve Markdown files with advanced cleaning and formatting.")
    parser.add_argument("input_file", help="Path to the input Markdown file")
    parser.add_argument("output_file", help="Path to the output improved Markdown file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--single-pass", action="store_true", help="Run only the first improvement pass")
    parser.add_argument("--log-file", help="Path to the log file")
    parser.add_argument("--log-level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
                        default='INFO', help="Set the logging level")
    parser.add_argument("--config", default="cleaning_config.yaml", help="Path to the cleaning configuration file")
    return parser.parse_args()

def setup_logging(args):
    log_level = getattr(logging, args.log_level)
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    if args.log_file:
        logging.basicConfig(filename=args.log_file, level=log_level, format=log_format)
    else:
        logging.basicConfig(level=log_level, format=log_format)

    if args.verbose:
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)

def main():
    args = parse_arguments()
    setup_logging(args)

    logging.info(f"Starting Markdown improvement process for {args.input_file}")

    if not os.path.exists(args.input_file):
        logging.error(f"Input file '{args.input_file}' does not exist.")
        sys.exit(1)

    config = load_config(args.config)
    logging.info(f"Loaded configuration from {args.config}")

    try:
        # Step 1: Improve Markdown using the first method
        improve_markdown(args.input_file, args.output_file, config)
        logging.info(f"First pass: Improved Markdown has been written to {args.output_file}")

        if not args.single_pass:
            # Step 2: Further improve the Markdown using the second method
            improve_markdown2(args.output_file, args.output_file, config)
            logging.info(f"Second pass: Further improved Markdown has been written to {args.output_file}")
        else:
            logging.info("Single pass mode: Skipping second improvement pass")

        logging.info("Markdown improvement completed successfully")

    except Exception as e:
        logging.exception(f"An error occurred while processing the file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
