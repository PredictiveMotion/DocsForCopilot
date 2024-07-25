from config_management import read_config
from utils.argument_parser import parse_arguments

def parse_arguments_and_configure_paths():
    args = parse_arguments()
    
    if args.config:
        config = read_config(args.config)
        return (
            config["PDFSettings"]["input_folder"],
            config["PDFSettings"]["output_folder"],
            config["PDFSettings"]["converter"]
        )
    
    return args.pdf_dir, args.md_dir, args.converter
