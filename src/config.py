"""Configuration settings for the PDF download script."""

import os

# Determine the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Constants
CHROME_DRIVER_PATH = os.path.join(PROJECT_ROOT, "chrome", "chrome_windows", "chromedriver.exe")
NUM_PROCESSES = 5
LOG_FILE = os.path.join(PROJECT_ROOT, "logs", "pdf_download.log")
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "downloaded_pdfs")
DEFAULT_LINKS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "scraped_links_netframework-4.5.2.txt")
# DEFAULT_LINKS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "framework452_links.txt")
REQUIREMENTS_DIR = os.path.join(PROJECT_ROOT, "requirements")
