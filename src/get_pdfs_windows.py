import sys
import os
import time
import logging
import argparse
import concurrent.futures
import requests
import json
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

def initialize_driver(download_dir):
    chrome_options = Options()
#    chrome_options.add_argument("--headless")
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



import requests
from urllib.parse import urljoin, urlparse, parse_qs

def download_pdf(driver, link, idx, download_dir):
    try:
        # Extract the PDF filename from the link
        parsed_url = urlparse(link)
        pdf_filename = parsed_url.path.split('/')[-1] + '.pdf'
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

        # Find and click the PDF download button
        try:
            pdf_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-bi-name='download-pdf']"))
            )
            pdf_button.click()
            logging.info(f"PDF button clicked for link {idx}")
        except Exception as e:
            logging.error(f"Failed to click PDF button for link {idx}: {str(e)}")
            return False

        # Wait for the PDF URL to appear in the browser's address bar
        def pdf_url_present(driver):
            return "pdf?url=" in driver.current_url

        try:
            WebDriverWait(driver, 10).until(pdf_url_present)
        except TimeoutException:
            logging.error(f"PDF URL not found in address bar for link {idx}")
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


# def download_pdf(driver, link, idx, download_dir):
#     try:
#         # Extract the PDF filename from the link
#         pdf_filename = link.split('/')[-1].split('?')[0] + '.pdf'
#         pdf_path = os.path.join(download_dir, pdf_filename)
#         crdownload_path = pdf_path + '.crdownload'

#         logging.info(f"Processing link {idx}: {link}")
#         logging.info(f"Expected PDF path: {pdf_path}")

#         # Check if the file already exists
#         if os.path.exists(pdf_path):
#             logging.info(f"PDF already exists for link {idx}: {pdf_filename}")
#             return True

#         # Navigate to the URL
#         logging.info(f"Navigating to URL: {link}")
#         driver.get(link)

#         # Wait for the page to load
#         WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

#         # Log the current URL to verify navigation
#         current_url = driver.current_url
#         logging.info(f"Current URL after navigation: {current_url}")

#         selectors = [
#             "//button[@data-bi-name='download-pdf']",
#             "//a[contains(@href, '.pdf')]",
#             "//button[contains(text(), 'Download PDF')]",
#             "//a[contains(text(), 'Download PDF')]",
#             "/html/body/div[2]/div/div/nav/div[2]/button",
#             "//*[@id='affixed-left-container']/div[2]/button",
#             "#affixed-left-container > div.padding-xxs.padding-none-tablet.border-top.border-bottom-tablet > button"
#         ]

#         for selector in selectors:
#             try:
#                 if selector.startswith("//"):
#                     pdf_button = WebDriverWait(driver, 10).until(
#                         EC.element_to_be_clickable((By.XPATH, selector))
#                     )
#                 else:
#                     pdf_button = WebDriverWait(driver, 10).until(
#                         EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
#                     )
#                 pdf_button.click()
#                 logging.info(f"PDF button found and clicked for link {idx} using selector: {selector}")

#                 # Wait for download to complete
#                 max_wait_time = 120  # Increased wait time to 2 minutes
#                 start_time = time.time()
#                 while time.time() - start_time < max_wait_time:
#                     if os.path.exists(pdf_path):
#                         if os.path.getsize(pdf_path) > 0:
#                             logging.info(f"Downloaded PDF for link {idx}: {pdf_filename}")
#                             return True
#                         else:
#                             os.remove(pdf_path)  # Remove empty PDF file
#                             logging.warning(f"Empty PDF file removed for link {idx}: {pdf_filename}")

#                     if not os.path.exists(crdownload_path):
#                         time.sleep(2)  # Wait a bit more to ensure download is complete
#                         break

#                     time.sleep(1)

#                 # Final check and cleanup
#                 if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
#                     logging.info(f"Successfully downloaded PDF for link {idx}: {pdf_filename}")
#             except TimeoutException as e:
#                 logging.warning(f"TimeoutException occurred for link {idx}: {str(e)}")
#                 continue

#             except NoSuchElementException as e:
#                 logging.warning(f"Selector {selector} not found for link {idx}: {str(e)}")
#                 # Capture the page source for debugging
#                 page_source = driver.page_source
#                 with open(f"debug_page_source_{idx}.html", "w", encoding="utf-8") as f:
#                     f.write(page_source)
#                 continue

#         logging.warning(f"No PDF button found for link {idx}. Skipping.")
#         return False
#     except WebDriverException as e:
#         logging.error(f"WebDriver error downloading PDF for link {idx}: {str(e)}")
#         return False
#     except Exception as e:
#         logging.error(f"Unexpected error downloading PDF for link {idx}: {str(e)}")
#         return False


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




def js_download(driver, idx):
    """Attempt to trigger the PDF download using JavaScript."""
    try:
        script = """
        var links = document.querySelectorAll('a[href*=".pdf"], button[data-bi-name="download-pdf"]');
        if (links.length > 0) {
            links[0].click();
            return true;
        }
        return false;
        """
        result = driver.execute_script(script)
        if result:
            logging.info(f"JavaScript-based download triggered for link {idx}")
            return True
        else:
            logging.warning(f"No suitable element found for JavaScript-based download for link {idx}")
            return False
    except JavascriptException as e:
        logging.error(f"JavaScript error during download attempt for link {idx}: {str(e)}")
        return False
    
  
def wait_for_download(driver, pdf_path, crdownload_path, idx, pdf_filename):
    """Wait for the PDF download to complete."""
    max_wait_time = 180  # 3 minutes
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        if check_download_complete(pdf_path, idx, pdf_filename):
            return True
        if os.path.exists(crdownload_path):
            time.sleep(5)
        else:
            time.sleep(10)
            if not os.path.exists(pdf_path) and not os.path.exists(crdownload_path):
                logging.warning(f"No download started for link {idx} after {time.time() - start_time:.2f} seconds")
                analyze_network_traffic(driver, idx)
                return False
    logging.warning(f"Download timed out for link {idx}: {pdf_filename}")
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



def check_for_js_errors(driver):
    """Check for JavaScript errors on the page."""
    try:
        logs = driver.get_log('browser')
        for log in logs:
            if log['level'] == 'SEVERE':
                logging.warning(f"JavaScript error detected: {log['message']}")
        return len([log for log in logs if log['level'] == 'SEVERE']) == 0
    except Exception as e:
        logging.error(f"Error checking for JavaScript errors: {str(e)}")
        return True

def direct_download(url, pdf_path, idx):
    """Attempt to download the PDF directly using requests."""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(pdf_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        logging.info(f"Direct download successful for link {idx}")
        return True
    except requests.RequestException as e:
        logging.error(f"Direct download failed for link {idx}: {str(e)}")
        return False


def check_pdf_availability(driver, idx):
    """Check if the PDF is available on the page."""
    try:
        pdf_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[@data-bi-name='download-pdf']"))
        )
        logging.info(f"PDF button found for link {idx}")
        return True
    except (TimeoutException, NoSuchElementException):
        logging.warning(f"PDF button not found for link {idx}")
        return False


def analyze_network_traffic(driver, idx):
    """Analyze network traffic for PDF download requests."""
    try:
        logs = driver.get_log('performance')
        for entry in logs:
            log = json.loads(entry['message'])['message']
            if 'Network.responseReceived' in log['method'] or 'Network.requestWillBeSent' in log['method']:
                url = log['params'].get('response', {}).get('url') or log['params'].get('request', {}).get('url')
                if url and url.endswith('.pdf'):
                    logging.info(f"PDF-related network activity detected for link {idx}: {url}")
                    return True
        logging.warning(f"No PDF-related network activity detected for link {idx}")
    except Exception as e:
        logging.error(f"Error analyzing network traffic for link {idx}: {str(e)}")
    return False

def capture_page_source(driver, idx):
    """Capture and log the page source after attempting to download."""
    try:
        page_source = driver.page_source
        logging.info(f"Page source for link {idx} after download attempt (first 500 characters):\n{page_source[:500]}...")
    except Exception as e:
        logging.error(f"Error capturing page source for link {idx}: {str(e)}")

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
    driver = initialize_driver(download_dir)

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




