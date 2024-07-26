"""Utility functions for the PDF download script."""

import os
import logging

def setup_logging(log_file):
    """Set up logging configuration."""
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.getLogger().setLevel(logging.INFO)

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
