import os
import sys
import configparser

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def read_config(config_file="config.ini"):
    """
    Reads configuration settings from a specified INI file.

    Args:
        config_file (str): Path to the configuration file. Defaults to 'config.ini'.

    Returns:
        configparser.ConfigParser: A ConfigParser object containing the configuration settings.
    """
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def get_config_settings(config_file):
    config = read_config(config_file)
    return (
        config["PDFSettings"]["input_folder"],
        config["PDFSettings"]["output_folder"],
        config["PDFSettings"]["converter"]
    )
