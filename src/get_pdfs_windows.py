"""Script to download PDFs from Microsoft .NET API documentation using Selenium WebDriver."""
import sys
import os
import time
import logging
import argparse
import concurrent.futures
from queue import Queue
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.utils.file_operations import rename_files_remove_splitted, cleanup_crdownload_files, file_exists, create_directory
from src.utils.webdriver_utils import create_driver_pool, cleanup_driver_pool
from src.utils.link_operations import read_links_from_file
from src.utils.logging_utils import setup_logging
from src.pdf_download import process_link_with_own_driver
from config import NUM_PROCESSES, LOG_FILE, DEFAULT_DOWNLOAD_DIR, DEFAULT_LINKS_FILE

print("Script started")

# Set up logging
setup_logging(LOG_FILE)
print("Logging set up")

# Initialize a queue for WebDriver instances
driver_queue = Queue()
print("Queue initialized")

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
            pdf_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, selector))
            )
            pdf_button.click()
            logging.info(f"PDF button found and clicked for link {idx} using selector: {selector}")
            return True
        except (TimeoutException, NoSuchElementException) as e:
            logging.warning(f"Selector {selector} not found for link {idx}: {str(e)}")
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
        time.sleep(10)  # Wait for page to load

        return download_pdf(driver, link, idx, download_dir)
    except WebDriverException as e:
        logging.error(f"WebDriver error processing link {idx}: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error processing link {idx}: {str(e)}")

    return False

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Download PDFs from a list of links.")
    parser.add_argument("--download_dir", help=f"Directory to save downloaded PDFs (default: {DEFAULT_DOWNLOAD_DIR})")
    parser.add_argument("--links_file", help=f"File containing links to process (default: {DEFAULT_LINKS_FILE})")
    return parser.parse_args()

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
            futures = [executor.submit(process_link_with_own_driver, (idx, link), download_dir, driver_queue) for idx, link in enumerate(links)]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Error in thread: {str(e)}")
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
