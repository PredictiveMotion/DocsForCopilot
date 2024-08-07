import re
import sys
import yaml
import argparse
import logging
import os

def load_config(config_file):
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logging.error(f"Error loading configuration file: {str(e)}")
        return {}

def remove_repetitive_text(content, patterns_to_remove):
    for pattern in patterns_to_remove:
        content = re.sub(pattern, "", content, flags=re.DOTALL | re.MULTILINE)
    return content

def remove_specific_lines(content):
    patterns_to_remove = [
        r'^\s*[\d\W]*Collaborate with us on.*$',
        r'^\s*[\d\W]*\.NET feedback.*$',
        r'^\s*[\d\W]*GitHub.*$',
        r'^\s*[\d\W]*\.NET is an open source project\..*$',
        r'^\s*[\d\W]*The source for this content can.*$',
        r'^\s*[\d\W]*Select a link to provide feedback:.*$',
        r'^\s*[\d\W]*be found on GitHub, where you.*$',
        r'^\s*[\d\W]*can also create and review.*$',
        r'^\s*[\d\W]*Open a documentation issue.*$',
        r'^\s*[\d\W]*issues and pull requests\. For.*$',
        r'^\s*[\d\W]*more information, see our.*$',
        r'^\s*[\d\W]*Provide product feedback.*$',
        r'^\s*[\d\W]*contributor guide\..*$',
        r'^\s*[\d\W]*Tell us about your PDF experience\..*$'
        

    ]
    
    cleaned_lines = []
    for line in content.split('\n'):
        if not any(re.match(pattern, line) for pattern in patterns_to_remove):
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def clean_markdown(input_file, output_file, config):
    try:
        logging.info(f"Starting cleaning process for {input_file}")
        
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read()
        logging.debug(f"Read {len(content)} characters from {input_file}")

        cleaned_content = remove_repetitive_text(content, config.get('patterns_to_remove', []))
        logging.debug("Removed repetitive text")

        cleaned_content = remove_specific_lines(cleaned_content)
        logging.debug("Removed specific lines")

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(cleaned_content)
        logging.info(f"Wrote cleaned Markdown to {output_file}")

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
    parser = argparse.ArgumentParser(description="Clean Markdown files by removing repetitive text.")
    parser.add_argument("input_file", help="Path to the input Markdown file")
    parser.add_argument("output_file", help="Path to the output cleaned Markdown file")
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

    logging.info(f"Starting Markdown cleaning process for {args.input_file}")

    if not os.path.exists(args.input_file):
        logging.error(f"Input file '{args.input_file}' does not exist.")
        sys.exit(1)

    config = load_config(args.config)
    logging.info(f"Loaded configuration from {args.config}")

    try:
        clean_markdown(args.input_file, args.output_file, config)
        logging.info("Markdown cleaning completed successfully")
    except Exception as e:
        logging.exception(f"An error occurred while processing the file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
