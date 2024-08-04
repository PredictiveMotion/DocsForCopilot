"""Utility functions for the PDF download script."""

import os
import logging
from config import PROJECT_ROOT

__all__ = ['setup_logging', 'file_exists', 'create_directory', 'read_links_from_file', 'get_absolute_path']

def file_exists(file_path):
    """Check if a file exists at the given path."""
    return os.path.exists(file_path)

def setup_logging(log_file):
    """Set up logging configuration."""
    print(f"Attempting to set up logging with log file: {log_file}")
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
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
    os.makedirs(directory, exist_ok=True)

def read_links_from_file(file_path):
    """Read links from a file and return a list of non-empty links."""
    with open(file_path, "r", encoding="utf-8") as file:
        return [link.strip() for link in file.readlines() if link.strip()]

def get_absolute_path(relative_path):
    """Convert a relative path to an absolute path based on the project root."""
    return os.path.join(PROJECT_ROOT, relative_path)
