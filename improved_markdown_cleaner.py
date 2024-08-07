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

def load_config(config_file):
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logging.error(f"Error loading configuration file: {str(e)}")
        return {}

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

def improve_language_spec(language, language_mapping):
    return language_mapping.get(language.lower(), language)

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
            logging.warning(f"Error parsing YAML frontmatter: {str(e)}")
        except Exception as e:
            logging.warning(f"Unexpected error processing frontmatter: {str(e)}")
    return None, content

def process_code_block(code_text, language):
    # Preserve original formatting, only add language specifier
    return f"```{language}\n{code_text}\n```\n\n"

def improve_markdown(input_file, output_file, config):
    try:
        logging.info(f"Starting improvement process for {input_file}")
        
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()
        logging.debug(f"Read {len(content)} characters from {input_file}")

        frontmatter, content = extract_frontmatter(content)
        if frontmatter:
            logging.debug("Extracted YAML frontmatter")

        # Pre-process headers to protect special characters
        def protect_headers(match):
            return f"{match.group(1)} {match.group(2).replace('#', '‡')}"
        
        content = re.sub(r'^(#+)\s+(.*?)$', protect_headers, content, flags=re.MULTILINE)

        html = markdown(content, extensions=[FencedCodeExtension(), "tables"])
        logging.debug("Converted Markdown to HTML")

        soup = BeautifulSoup(html, "html.parser")
        logging.debug("Parsed HTML with BeautifulSoup")

        improved_md = ""

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
                paragraph_content = re.sub(r'<strong>(.*?)</strong>', r'**\1**', paragraph_content)
                paragraph_content = re.sub(r'<em>(.*?)</em>', r'*\1*', paragraph_content)
                paragraph_content = re.sub(r'<a href="(.*?)">(.*?)</a>', r'[\2](\1)', paragraph_content)
                improved_md += f"{paragraph_content.strip()}\n\n"
            
            elif tag.name == "pre":
                code = tag.find("code")
                if code:
                    language = code.get("class", [""])[0].replace("language-", "")
                    language = improve_language_spec(language, config.get('language_mapping', {}))
                    # Preserve original formatting, including line breaks
                    improved_md += process_code_block(code.text, language)
            
            elif tag.name in ["ul", "ol"]:
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

        improved_md = improve_links(improved_md)
        logging.debug("Improved link formatting")

        improved_md = improve_images(improved_md)
        logging.debug("Improved image references")

        improved_md = re.sub(r"\n{3,}", "\n\n", improved_md)
        logging.debug("Removed extra newlines")

        improved_md = remove_repetitive_text(improved_md, config.get('patterns_to_remove', []))
        logging.debug("Removed repetitive text")

        # Restore protected characters in headers
        improved_md = improved_md.replace('‡', '#')

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
        improve_markdown(args.input_file, args.output_file, config)
        logging.info("Markdown improvement completed successfully")
    except Exception as e:
        logging.exception(f"An error occurred while processing the file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
