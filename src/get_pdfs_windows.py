import sys
import os
import time
import logging
import argparse
import concurrent.futures
import requests
import json
from queue import Queue
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
from src.utils.webdriver_utils import create_driver_pool, cleanup_driver_pool, initialize_driver
from src.utils.link_operations import read_links_from_file
from src.utils.logging_utils import setup_logging
from src.pdf_download import process_link_with_own_driver
from src.utils.argument_parser import parse_arguments
from config import NUM_PROCESSES, LOG_FILE, DEFAULT_DOWNLOAD_DIR, DEFAULT_LINKS_FILE

print("Script started")

# Set up logging
setup_logging(LOG_FILE)
print("Logging set up")

# Initialize a queue for WebDriver instances
driver_queue = Queue()
print("Queue initialized")



def download_pdf(driver, link, idx, download_dir):
    try:
        # Extract the PDF filename from the link
        pdf_filename = link.split('/')[-1].split('?')[0] + '.pdf'
        pdf_path = os.path.join(download_dir, pdf_filename)
        crdownload_path = pdf_path + '.crdownload'

        logging.info(f"Processing link {idx}: {link}")
        logging.info(f"Expected PDF path: {pdf_path}")

        # Check if the file already exists
        if os.path.exists(pdf_path):
            logging.info(f"PDF already exists for link {idx}: {pdf_filename}")
            return True

        selectors = [
            "//button[@data-bi-name='download-pdf']",
            "//a[contains(@href, '.pdf')]",
            "//button[contains(text(), 'Download PDF')]",
            "//a[contains(text(), 'Download PDF')]",
            "/html/body/div[2]/div/div/nav/div[2]/button",
            "//*[@id='affixed-left-container']/div[2]/button",
            "#affixed-left-container > div.padding-xxs.padding-none-tablet.border-top.border-bottom-tablet > button"
        ]

        for selector in selectors:
            try:
                if selector.startswith("//"):
                    pdf_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    pdf_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                pdf_button.click()
                logging.info(f"PDF button found and clicked for link {idx} using selector: {selector}")

                # Wait for download to complete
                max_wait_time = 120  # Increased wait time to 2 minutes
                start_time = time.time()
                while time.time() - start_time < max_wait_time:
                    if os.path.exists(pdf_path):
                        if os.path.getsize(pdf_path) > 0:
                            logging.info(f"Downloaded PDF for link {idx}: {pdf_filename}")
                            return True
                        else:
                            os.remove(pdf_path)  # Remove empty PDF file
                            logging.warning(f"Empty PDF file removed for link {idx}: {pdf_filename}")

                    if not os.path.exists(crdownload_path):
                        time.sleep(2)  # Wait a bit more to ensure download is complete
                        break

                    time.sleep(1)

                # Final check and cleanup
                if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                    logging.info(f"Successfully downloaded PDF for link {idx}: {pdf_filename}")
                    return True
                elif os.path.exists(crdownload_path):
                    os.remove(crdownload_path)
                    logging.warning(f"Removed incomplete download file for link {idx}: {pdf_filename}.crdownload")

                logging.warning(f"Failed to download PDF for link {idx}: {pdf_filename}")
                return False

            except (TimeoutException, NoSuchElementException) as e:
                logging.warning(f"Selector {selector} not found for link {idx}: {str(e)}")
                # Capture the page source for debugging
                page_source = driver.page_source
                with open(f"debug_page_source_{idx}.html", "w", encoding="utf-8") as f:
                    f.write(page_source)
                continue

        logging.warning(f"No PDF button found for link {idx}. Skipping.")
        return False
    except WebDriverException as e:
        logging.error(f"WebDriver error downloading PDF for link {idx}: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error downloading PDF for link {idx}: {str(e)}")
        return False


def click_pdf_button(driver, idx):
    """Attempt to click the PDF download button on the page."""
    selectors = [
        "//button[@data-bi-name='download-pdf']",
        "//a[contains(@href, '.pdf')]",
        "//button[contains(text(), 'Download PDF')]",
        "//a[contains(text(), 'Download PDF')]",
        "//button[contains(@class, 'download-pdf-button')]",
        "//a[contains(@class, 'download-pdf-link')]",
        "/html/body/div[2]/div/div/nav/div[2]/button",
        "//*[@id='affixed-left-container']/div[2]/button",
        "#affixed-left-container > div.padding-xxs.padding-none-tablet.border-top.border-bottom-tablet > button"
    ]
    for selector in selectors:
        try:
            logging.info(f"Attempting to find PDF button for link {idx} using selector: {selector}")
            pdf_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH if selector.startswith("//") or selector.startswith("/html") else By.CSS_SELECTOR, selector))
            )
            logging.info(f"PDF button found for link {idx} using selector: {selector}")
            driver.execute_script("arguments[0].click();", pdf_button)
            logging.info(f"PDF button clicked for link {idx}")
            return True
        except TimeoutException as e:
            logging.warning(f"TimeoutException occurred for link {idx}: {str(e)}")
        except NoSuchElementException as e:
            logging.warning(f"No such element found for link {idx}: {str(e)}")
            logging.warning(f"Selector {selector} not found for link {idx}: {str(e)}")
        except Exception as e:
            logging.error(f"General Error clicking PDF button for link {idx}: {str(e)}")
    
    logging.error(f"No PDF button found for link {idx}")
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
        try:
            if check_download_complete(pdf_path, idx, pdf_filename):
                return True
            if file_exists(crdownload_path):
                logging.info(f"Incomplete download file exists for link {idx}: {pdf_filename}.crdownload, waiting...")
                time.sleep(5)
            else:
                logging.info(f"No download file found for link {idx}: {pdf_filename}, waiting...")
                time.sleep(10)
                if not file_exists(pdf_path) and not file_exists(crdownload_path):
                    logging.warning(f"No download started for link {idx} after {time.time() - start_time:.2f} seconds")
                    analyze_network_traffic(driver, idx)
                    return False
        except UnexpectedAlertPresentException:
            logging.warning(f"Unexpected alert present for link {idx}. Attempting to close.")
            try:
                alert = driver.switch_to.alert
                alert.dismiss()
            except:
                pass
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

def process_link(driver, link, idx, download_dir):
    """Process a single link to download its PDF."""
    if not link.strip():
        logging.warning(f"Skipping empty link at index {idx}")
        return False

    try:
        logging.info(f"Processing link {idx}: {link}")
        driver.get(link)
        time.sleep(20)  # Wait for page to load

        if not check_for_js_errors(driver):
            logging.warning(f"JavaScript errors detected for link {idx}")

        # Check if PDF is available
        if not check_pdf_availability(driver, idx):
            logging.warning(f"PDF not available for link {idx}, attempting direct download")
            pdf_filename = link.split('/')[-1].split('?')[0] + '.pdf'
            pdf_path = os.path.join(download_dir, pdf_filename)
            if direct_download(link, pdf_path, idx):
                logging.info(f"Direct download succeeded for link {idx}")
                return True
            else:
                logging.error(f"Direct download failed for link {idx}")
                return False

        return download_pdf(driver, link, idx, download_dir)
    except WebDriverException as e:
        logging.error(f"WebDriver error processing link {idx}: {str(e)}")
        driver = reinitialize_driver(download_dir)
        if driver is not None:
            return process_link(driver, link, idx, download_dir)
    except Exception as e:
        logging.error(f"Unexpected error processing link {idx}: {str(e)}")

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

def create_driver_with_network_logging(download_dir):
    """Create a WebDriver instance with network logging enabled."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_experimental_option('prefs', {
        'download.default_directory': download_dir,
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'safebrowsing.enabled': False
    })
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL', 'browser': 'ALL'})
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def reinitialize_driver(download_dir):
    """Reinitialize the WebDriver after a crash."""
    try:
        return create_driver_with_network_logging(download_dir)
    except Exception as e:
        logging.error(f"Failed to reinitialize WebDriver: {str(e)}")
        return None

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
    print(f"Download directory: {download_dir}")
    print(f"Links file: {links_file}")

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

    print("Initializing WebDriver pool")
    #create_driver_pool(NUM_PROCESSES, download_dir, driver_queue, create_driver_with_network_logging)
    create_driver_pool(NUM_PROCESSES, download_dir, driver_queue, initialize_driver)



    print("Reading links from file")
    links = read_links_from_file(links_file)
    print(f"Number of links read: {len(links)}")

    # print("Starting download process")
    # try:
    #     with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_PROCESSES) as executor:
    #         futures = [executor.submit(process_link_with_own_driver, (idx, link), download_dir, driver_queue) for idx, link in enumerate(links)]
    #         for future in concurrent.futures.as_completed(futures):
    #             try:
    #                 future.result()
    #             except Exception as e:
    #                 logging.error(f"Error in thread: {str(e)}")
    # except Exception as e:
    #     print(f"Error during download process: {str(e)}")

    print("Starting download process")
    try:
        for idx, link in enumerate(links):
            driver = driver_queue.get()
            success = download_pdf(driver, link, idx, download_dir)
            driver_queue.put(driver)
            if not success:
                logging.warning(f"Failed to download PDF for link {idx}: {link}")
    except Exception as e:
        logging.error(f"Error during download process: {str(e)}")


    print("Download process completed")
    logging.info("Download process completed.")
    rename_files_remove_splitted(download_dir)
    cleanup_crdownload_files(download_dir)

    print("Cleaning up WebDriver instances")
    cleanup_driver_pool(driver_queue)

    print("Script execution completed")

if __name__ == "__main__":
    main()
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
