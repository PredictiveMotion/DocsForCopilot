
import configparser


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
