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
    """
    Load the cleaning configuration from a YAML file.

    Args:
        config_file (str): Path to the configuration file.

    Returns:
        dict: The loaded configuration.
    """
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logging.error(f"Error loading configuration file: {str(e)}")
        return {}

def process_blockquotes(soup):
    """
    Process blockquotes in the BeautifulSoup object and convert them to Markdown format.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the parsed HTML.

    Returns:
        str: A string containing the processed blockquotes in Markdown format.
    """
    blockquote_md = ""
    for blockquote in soup.find_all("blockquote"):
        blockquote_md += "> " + blockquote.text.strip().replace("\n", "\n> ") + "\n\n"
    return blockquote_md

def process_horizontal_rules(soup):
    """
    Process horizontal rules in the BeautifulSoup object and convert them to Markdown format.
    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the parsed HTML.
    Returns:
        str: A string containing the processed horizontal rules in Markdown format.
    """
    hr_md = ""
    for hr in soup.find_all("hr"):
        hr_md += "---\n\n"
    return hr_md

def process_nested_lists(ul_or_ol, indent=""):
    """
    Process nested lists in the BeautifulSoup object and convert them to Markdown format.

    Args:
        ul_or_ol (Tag): The BeautifulSoup Tag object representing an unordered or ordered list.
        indent (str, optional): The current indentation level. Defaults to "".

    Returns:
        str: A string containing the processed nested lists in Markdown format.
    """
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
    """
    Improve the language specification for code blocks.

    Args:
        language (str): The original language specification.

    Returns:
        str: The improved language specification.
    """
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
    """
    Improve the formatting of links in the Markdown content.

    Args:
        content (str): The Markdown content containing links.

    Returns:
        str: The Markdown content with improved link formatting.
    """
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
    """
    Improve the formatting of image references in the Markdown content.

    Args:
        content (str): The Markdown content containing image references.

    Returns:
        str: The Markdown content with improved image reference formatting.
    """
    # Improve inline images
    content = re.sub(
        r"!\[([^\]]*)\]\(([^\)]+)\)",
        lambda m: f"![{m.group(1).strip()}]({m.group(2).strip()})",
        content,
    )

    return content

def remove_repetitive_text(content, patterns_to_remove):
    """
    Remove repetitive text patterns from the Markdown content.

    Args:
        content (str): The Markdown content containing potentially repetitive text.
        patterns_to_remove (list): List of patterns to remove from the content.

    Returns:
        str: The Markdown content with repetitive text patterns removed.
    """
    for pattern in patterns_to_remove:
        content = re.sub(pattern, "", content, flags=re.DOTALL | re.MULTILINE)

    return content

def extract_frontmatter(content):
    """
    Extract YAML frontmatter from the Markdown content.

    Args:
        content (str): The Markdown content potentially containing YAML frontmatter.

    Returns:
        tuple: A tuple containing the extracted frontmatter (dict or None) and the remaining content (str).
    """
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
    """
    Improve the Markdown content in the input file and write the result to the output file.

    This function performs various improvements on the Markdown content, including:
    - Extracting and processing YAML frontmatter
    - Converting Markdown to HTML and back to improved Markdown
    - Processing headings, paragraphs, code blocks, lists, and tables
    - Improving link and image formatting
    - Removing repetitive text and extra newlines

    Args:
        input_file (str): The path to the input Markdown file.
        output_file (str): The path to the output improved Markdown file.
        config (dict): The cleaning configuration.
    """
    logging.info(f"Starting second improvement pass for {input_file}")
    
    # Read the input file
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()
    logging.debug(f"Read {len(content)} characters from {input_file}")

    # Extract and process YAML frontmatter
    frontmatter, content = extract_frontmatter(content)
    if frontmatter:
        logging.debug("Extracted YAML frontmatter")

    # Convert Markdown to HTML
    html = markdown(content, extensions=["fenced_code", "tables"])
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

    # Process headings and ensure consistent levels
    heading_stack = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        level = int(tag.name[1])
        while heading_stack and heading_stack[-1] >= level:
            heading_stack.pop()
        if not heading_stack:
            heading_stack.append(level)
        elif level > heading_stack[-1]:
            heading_stack.append(min(heading_stack[-1] + 1, 6))
        adjusted_level = len(heading_stack)
        improved_md += f"{'#' * adjusted_level} {tag.text.strip()}\n\n"
    logging.debug("Processed headings and ensured consistent levels")
        
    # Store the original order of headings
    original_headings = [(tag.name, tag.text.strip()) for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])]
        
    # Reorder the improved_md content to match the original heading order
    reordered_md = ""
    for heading in original_headings:
        level, text = heading
        heading_pattern = r"^#{1,6} " + re.escape(text) + "$"
        match = re.search(heading_pattern, improved_md, re.MULTILINE)
        if match:
            reordered_md += match.group() + "\n\n"
            improved_md = improved_md[:match.start()] + improved_md[match.end():]
    
    improved_md = reordered_md + improved_md
    logging.debug("Reordered headings to match original order")

    # Process paragraphs
    for p in soup.find_all("p"):
        improved_md += f"{p.text.strip()}\n\n"
    logging.debug("Processed paragraphs")

    # Process code blocks with improved language specification
    for pre in soup.find_all("pre"):
        code = pre.find("code")
        if code:
            language = code.get("class", [""])[0].replace("language-", "")
            language = improve_language_spec(language, config.get('language_mapping', {}))
            improved_md += f"```{language}\n{code.text.strip()}\n```\n\n"
    logging.debug("Processed code blocks with improved language specification")

    # Process lists
    for ul in soup.find_all("ul"):
        for li in ul.find_all("li"):
            improved_md += f"- {li.text.strip()}\n"
        improved_md += "\n"

    for ol in soup.find_all("ol"):
        for i, li in enumerate(ol.find_all("li"), 1):
            improved_md += f"{i}. {li.text.strip()}\n"
        improved_md += "\n"
    logging.debug("Processed lists")

    # Process tables
    for table in soup.find_all("table"):
        headers = [th.text.strip() for th in table.find_all("th")]
        improved_md += "| " + " | ".join(headers) + " |\n"
        improved_md += "| " + " | ".join(["---"] * len(headers)) + " |\n"

        for row in table.find_all("tr")[1:]:
            cells = [td.text.strip() for td in row.find_all("td")]
            improved_md += "| " + " | ".join(cells) + " |\n"
        improved_md += "\n"
    logging.debug("Processed tables")

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

def improve_markdown(input_file, output_file):
    """
    Improve the Markdown content in the input file and write the result to the output file.

    This function performs various improvements on the Markdown content, including:
    - Extracting and processing YAML frontmatter
    - Converting Markdown to HTML and back to improved Markdown
    - Processing headings, paragraphs, code blocks, lists, tables, blockquotes, and horizontal rules
    - Improving link and image formatting
    - Removing repetitive text and extra newlines

    Args:
        input_file (str): The path to the input Markdown file.
        output_file (str): The path to the output improved Markdown file.

    Raises:
        FileNotFoundError: If the input file is not found.
        PermissionError: If there's a permission issue accessing the input or output file.
        Exception: For any other unexpected errors during processing.
    """
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

        # Process headings
        for i in range(1, 7):
            for heading in soup.find_all(f"h{i}"):
                improved_md += f"{'#' * i} {heading.text.strip()}\n\n"
        logging.debug("Processed headings")

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
        logging.debug("Processed paragraphs")

        # Process code blocks
        for pre in soup.find_all("pre"):
            code = pre.find("code")
            if code:
                language = code.get("class", [""])[0].replace("language-", "")
                language = improve_language_spec(language)
                improved_md += f"```{language}\n{code.text.strip()}\n```\n\n"
        logging.debug("Processed code blocks")

        # Process lists
        for ul in soup.find_all("ul", recursive=False):
            improved_md += process_nested_lists(ul)
            improved_md += "\n"
        for ol in soup.find_all("ol", recursive=False):
            improved_md += process_nested_lists(ol)
            improved_md += "\n"
        logging.debug("Processed lists")

        # Process tables
        for table in soup.find_all("table"):
            headers = [th.text.strip() for th in table.find_all("th")]
            improved_md += "| " + " | ".join(headers) + " |\n"
            improved_md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
            for row in table.find_all("tr")[1:]:
                cells = [td.text.strip() for td in row.find_all("td")]
                improved_md += "| " + " | ".join(cells) + " |\n"
            improved_md += "\n"
        logging.debug("Processed tables")

        # Process blockquotes
        improved_md += process_blockquotes(soup)
        logging.debug("Processed blockquotes")

        # Process horizontal rules
        improved_md += process_horizontal_rules(soup)
        logging.debug("Processed horizontal rules")

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
        improved_md = remove_repetitive_text(improved_md)
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
    """
    Parse command-line arguments for the improved Markdown cleaner script.

    Returns:
        argparse.Namespace: An object containing the parsed arguments.
    """
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
    """
    Set up logging based on the command-line arguments.

    Args:
        args (argparse.Namespace): The parsed command-line arguments.
    """
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
    """
    Main function to run the improved Markdown cleaner script.

    This function parses command-line arguments, sets up logging, checks for the existence of the input file,
    and runs both improvement methods (improve_markdown and improve_markdown2) on the input file.

    Usage:
        python improved_markdown_cleaner.py <input_file> <output_file> [options]

    Args:
        None (uses argparse for command-line arguments)

    Returns:
        None
    """
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
