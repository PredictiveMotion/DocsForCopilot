"""Utility functions for the PDF download script."""

import os
import logging

def setup_logging(log_file):
    """Set up logging configuration."""
    print(f"Attempting to set up logging with log file: {log_file}")
    try:
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        logging.getLogger().setLevel(logging.INFO)
        print(f"Logging setup completed. Log file should be at: {log_file}")
        logging.info("Logging initialized successfully")
    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Log file directory exists: {os.path.exists(os.path.dirname(log_file))}")
        print(f"Log file is writable: {os.access(os.path.dirname(log_file), os.W_OK)}")

def file_exists(file_path):
    """Check if a file exists at the given path."""
    return os.path.exists(file_path)

def create_directory(directory):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def read_links_from_file(file_path):
    """Read links from a file and return a list of non-empty links."""
    with open(file_path, "r", encoding="utf-8") as file:
        return [link.strip() for link in file.readlines() if link.strip()]
