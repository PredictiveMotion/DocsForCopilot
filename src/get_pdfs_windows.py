import sys
import os
import time
import logging
import argparse
import concurrent.futures
import requests
import json
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, JavascriptException, UnexpectedAlertPresentException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.utils.file_operations import rename_files_remove_splitted, cleanup_crdownload_files, file_exists, create_directory
from selenium.webdriver.chrome.options import Options

def initialize_driver(download_dir, headless=False):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-site-isolation-trials")
    chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")
    chrome_options.add_argument("--disable-safe-browsing")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--enable-javascript")
    chrome_options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": False,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "profile.default_content_setting_values.notifications": 2,
    })

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

from src.utils.link_operations import read_links_from_file
from src.utils.logging_utils import setup_logging
from src.pdf_download import process_link_with_own_driver
from src.utils.argument_parser import parse_arguments
from config import LOG_FILE, DEFAULT_DOWNLOAD_DIR, DEFAULT_LINKS_FILE

print("Script started")

# Set up logging
setup_logging(LOG_FILE)
print("Logging set up")

def download_pdf(driver, link, idx, download_dir):
    try:
        # Extract the PDF filename from the link
        parsed_url = urlparse(link)
        pdf_filename = parsed_url.path.split('/')[-1]
        if not pdf_filename:
            pdf_filename = f'default_{idx}'
        pdf_filename += '.pdf'
        pdf_path = os.path.join(download_dir, pdf_filename)

        logging.info(f"Processing link {idx}: {link}")
        logging.info(f"Expected PDF path: {pdf_path}")

        # Check if the file already exists
        if os.path.exists(pdf_path):
            logging.info(f"PDF already exists for link {idx}: {pdf_filename}")
            return True

        # Navigate to the URL
        logging.info(f"Navigating to URL: {link}")
        driver.get(link)

        # Wait for the page to load
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Log the current URL to verify navigation
        current_url = driver.current_url
        logging.info(f"Current URL after navigation: {current_url}")

        # Find and click the PDF download button
        try:
            pdf_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-bi-name='download-pdf']"))
            )
            driver.execute_script("arguments[0].click();", pdf_button)
            logging.info(f"PDF button clicked for link {idx}")
        except Exception as e:
            logging.error(f"Failed to click PDF button for link {idx}: {str(e)}")
            return False

        # Wait for the PDF URL to appear in the browser's address bar
        def pdf_url_present(driver):
            return "pdf?url=" in driver.current_url

        try:
            WebDriverWait(driver, 20).until(pdf_url_present)
        except TimeoutException:
            logging.error(f"PDF URL not found in address bar for link {idx}")
            # Attempt to get PDF URL from JavaScript
            try:
                pdf_url = driver.execute_script("return window.location.href;")
                if "pdf?url=" not in pdf_url:
                    logging.error(f"PDF URL not found in JavaScript for link {idx}")
                    return False
            except JavascriptException:
                logging.error(f"Failed to get PDF URL from JavaScript for link {idx}")
                return False

        # Extract the PDF URL
        pdf_url = driver.current_url
        logging.info(f"PDF URL for link {idx}: {pdf_url}")

        # Download the PDF using requests
        response = requests.get(pdf_url, stream=True, timeout=30)
        response.raise_for_status()

        with open(pdf_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
            logging.info(f"Successfully downloaded PDF for link {idx}: {pdf_filename}")
            return True
        else:
            logging.warning(f"Downloaded file is empty for link {idx}: {pdf_filename}")
            return False

    except Exception as e:
        logging.error(f"Error downloading PDF for link {idx}: {str(e)}")
        return False

def main():
    """Main function to orchestrate the PDF download process."""
    print("Entering main function")
    args = parse_arguments()
    print(f"Arguments parsed: {args}")

    download_dir = args.download_dir or DEFAULT_DOWNLOAD_DIR
    links_file = args.links_file or DEFAULT_LINKS_FILE
    parallel = args.parallel
    num_processes = args.num_processes if parallel else 1
    print(f"Download directory: {download_dir}")
    print(f"Links file: {links_file}")
    print(f"Parallel processing: {'Enabled' if parallel else 'Disabled'}")
    print(f"Number of processes: {num_processes}")

    # Check if download directory exists and is writable
    if not os.path.exists(download_dir):
        try:
            os.makedirs(download_dir)
            print(f"Created download directory: {download_dir}")
        except OSError as e:
            logging.error(f"Failed to create download directory: {str(e)}")
            print(f"Error: Failed to create download directory: {str(e)}")
            return

    if not os.access(download_dir, os.W_OK):
        logging.error(f"No write permission for download directory: {download_dir}")
        print(f"Error: No write permission for download directory: {download_dir}")
        return

    print("Initializing WebDriver")
    driver = initialize_driver(download_dir, headless=True)  # Set headless to True

    print("Reading links from file")
    links = read_links_from_file(links_file)
    print(f"Number of links read: {len(links)}")

    print("Starting download process")
    try:
        for idx, link in enumerate(links):
            success = download_pdf(driver, link, idx, download_dir)
            if not success:
                logging.warning(f"Failed to download PDF for link {idx}: {link}")
    except Exception as e:
        logging.error(f"Error during download process: {str(e)}")

    print("Download process completed")
    logging.info("Download process completed.")
    rename_files_remove_splitted(download_dir)
    cleanup_crdownload_files(download_dir)

    print("Cleaning up WebDriver instance")
    driver.quit()

    print("Script execution completed")

if __name__ == "__main__":
    main()
