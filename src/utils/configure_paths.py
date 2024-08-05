from config_management import read_config

def get_config_settings(config_file):
    config = read_config(config_file)
    return (
        config["PDFSettings"]["input_folder"],
        config["PDFSettings"]["output_folder"],
        config["PDFSettings"]["converter"]
    )
