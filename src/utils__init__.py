from .logging_utils import setup_logging
from ..utils import create_directory, read_links_from_file, get_absolute_path

def file_exists(file_path):
    """Check if a file exists at the given path."""
    import os
    return os.path.exists(file_path)
