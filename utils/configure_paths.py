import sys
from config_management import read_config
from utils.argument_parser import parse_arguments

def get_config_settings(config_file):
    config = read_config(config_file)
    return (
        config["PDFSettings"]["input_folder"],
        config["PDFSettings"]["output_folder"],
        config["PDFSettings"]["converter"]
    )

def get_cli_settings(args):
    if not args.pdf_dir or not args.md_dir:
        print("Usage: python pdfconvert.py <pdf_dir> <md_dir> [converter] OR --config <config.ini>")
        sys.exit(1)
    return args.pdf_dir, args.md_dir, args.converter

def configure_paths_and_converter(args):
    if args.config:
        return get_config_settings(args.config)
    return get_cli_settings(args)

def parse_arguments_and_configure_paths():
    args = parse_arguments()
    return configure_paths_and_converter(args)
