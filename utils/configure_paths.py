import sys
from config_management import read_config
from utils.argument_parser import parse_arguments

def configure_paths_and_converter(args):
    if args.config:
        config = read_config(args.config)
        pdf_directory = config["PDFSettings"]["input_folder"]
        markdown_directory = config["PDFSettings"]["output_folder"]
        converter_to_use = config["PDFSettings"]["converter"]
    else:
        if not args.pdf_dir or not args.md_dir:
            print(
                "Usage: python pdfconvert.py <pdf_dir> <md_dir> [converter] OR --config <config.ini>"
            )
            sys.exit(1)

        pdf_directory = args.pdf_dir
        markdown_directory = args.md_dir
        converter_to_use = args.converter
    return pdf_directory, markdown_directory, converter_to_use

def parse_arguments_and_configure_paths():
    args = parse_arguments()
    pdf_directory, markdown_directory, converter_to_use = configure_paths_and_converter(args)
    return pdf_directory, markdown_directory, converter_to_use
