"""Script to download PDFs from Microsoft .NET API documentation using Selenium WebDriver."""

import os
import time
import logging
import argparse
import threading
from queue import Queue
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)

from config import (
    CHROME_DRIVER_PATH,
    NUM_PROCESSES,
    LOG_FILE,
    DEFAULT_DOWNLOAD_DIR,
    DEFAULT_LINKS_FILE,
)
from utils import (
    setup_logging,
    file_exists,
    create_directory,
    read_links_from_file,
)

# Create log directory if it doesn't exist
log_dir = os.path.dirname(LOG_FILE)
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
from webdriver_utils import (
    initialize_driver,
    create_driver_pool,
    cleanup_driver_pool,
)
from pdf_download import (
    click_pdf_button,
    check_download_complete,
    cleanup_and_check,
    wait_for_download,
    download_pdf,
    process_link,
    process_link_with_own_driver,
)
from file_operations import (
    rename_files_remove_splitted,
    handle_permission_error,
    remove_crdownload_file,
    cleanup_crdownload_files,
)

# Constants and global variables
driver_queue = Queue()
file_lock = threading.Lock()

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Download PDFs from a list of links.")
    parser.add_argument("--download_dir", help="Directory to save downloaded PDFs")
    parser.add_argument("--links_file", help="File containing links to process")
    return parser.parse_args()

def setup_environment(download_dir):
    """Set up the environment for PDF downloads."""
    setup_logging(LOG_FILE)
    create_directory(download_dir)
    create_driver_pool(NUM_PROCESSES, download_dir, driver_queue)

def process_links(links, download_dir):
    """Process links using a thread pool."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_PROCESSES) as executor:
        list(
            executor.map(
                lambda x: process_link_with_own_driver(x, download_dir, driver_queue),
                enumerate(links, start=1),
            )
        )

def cleanup_environment(download_dir):
    """Perform cleanup operations after processing."""
    logging.info("Download process completed.")
    rename_files_remove_splitted(download_dir)
    cleanup_crdownload_files(download_dir)
    cleanup_driver_pool(driver_queue)

def main():
    """Main function to orchestrate the PDF download process."""
    args = parse_arguments()
    download_dir = args.download_dir or DEFAULT_DOWNLOAD_DIR
    links_file = args.links_file or DEFAULT_LINKS_FILE

    setup_environment(download_dir)
    links = read_links_from_file(links_file)
    process_links(links, download_dir)
    cleanup_environment(download_dir)

if __name__ == "__main__":
    main()
