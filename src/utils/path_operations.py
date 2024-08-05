import os

def get_absolute_path(relative_path):
    """Convert a relative path to an absolute path."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', relative_path))
