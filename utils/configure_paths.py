from config_management import read_config
from utils.argument_parser import parse_arguments

def get_config_settings(config_file):
    config = read_config(config_file)
    return (
        config["PDFSettings"]["input_folder"],
        config["PDFSettings"]["output_folder"],
        config["PDFSettings"]["converter"]
    )

def configure_paths_and_converter(args):
    if args.config:
        return get_config_settings(args.config)
    return args.pdf_dir, args.md_dir, args.converter

def parse_arguments_and_configure_paths():
    args = parse_arguments()
    return configure_paths_and_converter(args)
