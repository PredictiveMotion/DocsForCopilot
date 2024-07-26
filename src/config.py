"""Configuration settings for the PDF download script."""

import os

# Constants
CHROME_DRIVER_PATH = os.path.join("..", "chrome", "chrome_windows", "chromedriver.exe")
NUM_PROCESSES = 5
LOG_FILE = os.path.join("..", "logs", "pdf_download.log")
DEFAULT_DOWNLOAD_DIR = os.path.join("..", "data", "downloaded_pdfs")
DEFAULT_LINKS_FILE = os.path.join("..", "data", "framework452_links.txt")
