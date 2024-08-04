# src/get_pdfs_windows.py

"""Script to download PDFs from Microsoft .NET API documentation using Selenium WebDriver."""

import os
import sys
import time
import logging
import argparse
import concurrent.futures
from queue import Queue
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from config import CHROME_DRIVER_PATH, NUM_PROCESSES, LOG_FILE, DEFAULT_DOWNLOAD_DIR, DEFAULT_LINKS_FILE
from src.utils import file_exists, create_directory, read_links_from_file, get_absolute_path
from src.utils.webdriver_utils import initialize_driver, create_driver_pool, cleanup_driver_pool
from src.pdf_download import process_link_with_own_driver
from src.utils.file_operations import rename_files_remove_splitted, cleanup_crdownload_files

print("Script started")


# Set up logging
setup_logging(LOG_FILE)
print("Logging set up")

# Initialize a queue for WebDriver instances
driver_queue = Queue()
print("Queue initialized")


# def initialize_driver(download_dir):
#     """Initialize and configure a Chrome WebDriver instance."""
#     print("Initializing WebDriver")
#     options = Options()
#     options.add_argument("--headless")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--window-size=1920,1080")
#     options.add_argument("--disable-web-security")
#     options.add_argument("--allow-running-insecure-content")

#     # Set up download preferences
#     prefs = {
#         "download.default_directory": os.path.abspath(download_dir),
#         "download.prompt_for_download": False,
#         "download.directory_upgrade": True,
#         "plugins.always_open_pdf_externally": True,
#     }
#     options.add_experimental_option("prefs", prefs)

#     service = Service(executable_path=CHROME_DRIVER_PATH)

#     try:
#         print("Creating Chrome WebDriver instance")
#         driver = webdriver.Chrome(service=service, options=options)
#         driver.set_page_load_timeout(30)
#         logging.info("WebDriver initialized successfully")
#         print("WebDriver initialized successfully")
#         return driver
#     except Exception as e:
#         error_message = f"Failed to initialize WebDriver: {str(e)}"
#         logging.error(error_message)
#         print(error_message)
#         print(f"ChromeDriver path: {CHROME_DRIVER_PATH}")
#         print(f"Chrome version: {webdriver.chrome.service.get_chrome_version()}")
#         return None


def download_pdf(driver, link, idx, download_dir):
    """Attempt to download a PDF from the given link."""
    pdf_filename = link.split("/")[-1].split("?")[0] + ".pdf"
    pdf_path = os.path.join(download_dir, pdf_filename)
    crdownload_path = os.path.join(download_dir, f"{pdf_filename}.crdownload")

    if file_exists(pdf_path):
        logging.info(f"PDF already exists for link {idx}: {pdf_filename}")
        return True

    if click_pdf_button(driver, idx):
        return wait_for_download(pdf_path, crdownload_path, idx, pdf_filename)

    logging.warning(f"No PDF button found for link {idx}. Skipping.")
    return False

# def file_exists(file_path):
#     """Check if a file exists at the given path."""
#     return os.path.exists(file_path)

def click_pdf_button(driver, idx):
    """Attempt to click the PDF download button on the page."""
    selectors = [
        "//button[@data-bi-name='download-pdf']",
        "//a[contains(@href, '.pdf')]",
        "//button[contains(text(), 'Download PDF')]",
        "//a[contains(text(), 'Download PDF')]",
    ]
    for selector in selectors:
        try:
            pdf_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, selector))
            )
            pdf_button.click()
            logging.info(f"PDF button found and clicked for link {idx} using selector: {selector}")
            return True
        except (TimeoutException, NoSuchElementException):
            logging.warning(f"Selector {selector} not found for link {idx}")
    return False

def wait_for_download(pdf_path, crdownload_path, idx, pdf_filename):
    """Wait for the PDF download to complete."""
    max_wait_time = 300  # 5 minutes
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        if check_download_complete(pdf_path, idx, pdf_filename):
            return True
        if file_exists(crdownload_path):
            time.sleep(2)
        else:
            time.sleep(5)
            break
    return cleanup_and_check(pdf_path, crdownload_path, idx, pdf_filename)

def check_download_complete(pdf_path, idx, pdf_filename):
    """Check if the PDF download has completed successfully."""
    if os.path.exists(pdf_path):
        if os.path.getsize(pdf_path) > 0:
            logging.info(f"Downloaded PDF for link {idx}: {pdf_filename}")
            return True
        else:
            os.remove(pdf_path)
            logging.warning(f"Empty PDF file removed for link {idx}: {pdf_filename}")
    return False

def cleanup_and_check(pdf_path, crdownload_path, idx, pdf_filename):
    """Perform final cleanup and check if the download was successful."""
    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
        logging.info(f"Successfully downloaded PDF for link {idx}: {pdf_filename}")
        return True
    if os.path.exists(crdownload_path):
        os.remove(crdownload_path)
        logging.warning(f"Removed incomplete download file for link {idx}: {pdf_filename}.crdownload")
    logging.warning(f"Failed to download PDF for link {idx}: {pdf_filename}")
    return False


def process_link(driver, link, idx, download_dir):
    """Process a single link to download its PDF."""
    if not link.strip():
        logging.warning(f"Skipping empty link at index {idx}")
        return False

    try:
        logging.info(f"Processing link {idx}: {link}")
        driver.get(link)
        time.sleep(5)  # Wait for page to load

        return download_pdf(driver, link, idx, download_dir)
    except WebDriverException as e:
        logging.error(f"WebDriver error processing link {idx}: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error processing link {idx}: {str(e)}")

    return False


# def create_driver_pool(num_instances, download_dir, driver_queue):
#     """Create a pool of WebDriver instances."""
#     print(f"Creating driver pool with {num_instances} instances")
#     for i in range(num_instances):
#         print(f"Initializing driver {i+1}/{num_instances}")
#         driver = initialize_driver(download_dir)
#         if driver:
#             driver_queue.put(driver)
#             print(f"Driver {i+1} added to the pool")
#         else:
#             print(f"Failed to initialize driver {i+1}")
#     print(f"Driver pool created with {driver_queue.qsize()} instances")


def process_link_with_own_driver(link_idx_tuple, download_dir, driver_queue):
    """Process a link using a WebDriver instance from the pool."""
    idx, link = link_idx_tuple
    driver = driver_queue.get()  # Borrow a WebDriver instance from the pool
    try:
        success = process_link(driver, link, idx, download_dir)
        if not success:
            logging.warning(f"Failed to process link {idx}. Moving to next link.")
    finally:
        driver_queue.put(driver)  # Return the WebDriver instance to the pool


def rename_files_remove_splitted(download_dir):
    """Rename downloaded files to remove '_splitted' from their names."""
    downloaded_files = os.listdir(download_dir)
    for file_name in downloaded_files:
        if "_splitted" in file_name:
            new_file_name = file_name.replace("_splitted-", "")
            original_path = os.path.join(download_dir, file_name)
            new_path = os.path.join(download_dir, new_file_name)
            try:
                os.rename(original_path, new_path)
                logging.info(f"Renamed {file_name} to {new_file_name}")
            except Exception as e:
                logging.error(
                    f"Error renaming file {file_name} to {new_file_name}: {e}"
                )


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Download PDFs from a list of links.")
    parser.add_argument("--download_dir", help=f"Directory to save downloaded PDFs (default: {DEFAULT_DOWNLOAD_DIR})")
    parser.add_argument("--links_file", help=f"File containing links to process (default: {DEFAULT_LINKS_FILE})")
    return parser.parse_args()



def cleanup_crdownload_files(download_dir):
    """Remove any leftover .crdownload files in the download directory."""
    for filename in os.listdir(download_dir):
        if filename.endswith(".crdownload"):
            remove_crdownload_file(download_dir, filename)

def remove_crdownload_file(download_dir, filename):
    """Attempt to remove a specific .crdownload file."""
    file_path = os.path.join(download_dir, filename)
    for attempt in range(3):  # Try 3 times
        try:
            os.remove(file_path)
            logging.info(f"Removed leftover .crdownload file: {filename}")
            return
        except PermissionError:
            handle_permission_error(filename, attempt)
        except Exception as e:
            logging.error(f"Error removing .crdownload file {filename}: {str(e)}")
            return

def handle_permission_error(filename, attempt):
    """Handle permission errors when trying to remove a file."""
    if attempt < 2:  # If it's not the last attempt
        logging.warning(f"File {filename} is still in use. Retrying in 5 seconds...")
        time.sleep(5)
    else:
        logging.warning(f"File {filename} is still in use after 3 attempts. Skipping removal.")


def main():
    """Main function to orchestrate the PDF download process."""
    print("Entering main function")
    args = parse_arguments()
    print(f"Arguments parsed: {args}")

    download_dir = args.download_dir or DEFAULT_DOWNLOAD_DIR
    links_file = args.links_file or DEFAULT_LINKS_FILE
    print(f"Download directory: {download_dir}")
    print(f"Links file: {links_file}")

    create_directory(download_dir)
    print(f"Ensured download directory exists: {download_dir}")

    print("Initializing WebDriver pool")
    create_driver_pool(NUM_PROCESSES, download_dir, driver_queue)

    print("Reading links from file")
    links = read_links_from_file(links_file)
    print(f"Number of links read: {len(links)}")

    print("Starting download process")
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_PROCESSES) as executor:
            list(
                executor.map(
                    lambda x: process_link_with_own_driver(x, download_dir, driver_queue),
                    enumerate(links, start=1),
                )
            )
    except Exception as e:
        print(f"Error during download process: {str(e)}")

    print("Download process completed")
    logging.info("Download process completed.")
    rename_files_remove_splitted(download_dir)
    cleanup_crdownload_files(download_dir)

    print("Cleaning up WebDriver instances")
    cleanup_driver_pool(driver_queue)

    print("Script execution completed")

if __name__ == "__main__":
    main()
