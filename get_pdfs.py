import os
import time
import logging
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
from queue import Queue
import concurrent.futures

# Constants
NUM_PROCESSES = 5
DOWNLOAD_DIR = "downloaded_pdfs"
LINKS_FILE = "framework452_links.txt"
LOG_FILE = "pdf_download.log"

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Initialize a queue for WebDriver instances
driver_queue = Queue()


def get_os_specific_paths():
    """Determines the paths for the ChromeDriver and Chrome binary based on the operating system."""
    if platform.system() == "Linux":
        chrome_driver_path = "./chrome_linux/chromedriver"
        binary_location = os.path.abspath("chrome_linux/chrome-linux64/chrome")
    elif platform.system() == "Windows":
        chrome_driver_path = "c:/development/samples/pdfToMarkdown/chromedriver.exe"
        binary_location = None
    else:
        raise NotImplementedError("This script only supports Linux and Windows")
    return chrome_driver_path, binary_location


def initialize_driver():
    """Initializes and returns a Chrome WebDriver instance with predefined options."""
    chrome_driver_path, binary_location = get_os_specific_paths()
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    if binary_location:
        options.binary_location = binary_location
    options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": os.path.abspath(DOWNLOAD_DIR),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
        },
    )
    service = Service(executable_path=chrome_driver_path)
    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        logging.info("WebDriver initialized successfully")
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize WebDriver: {str(e)}")
        return None


def download_pdf(driver, link, idx):
    """Attempts to download a PDF from the given link and returns True if successful."""
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
            logging.info(
                f"PDF button clicked for link {idx} using selector: {selector}"
            )
            time.sleep(10)  # Adjust based on typical download duration
            if any(f.endswith(".pdf") for f in os.listdir(DOWNLOAD_DIR)):
                logging.info(f"Downloaded PDF for link {idx}")
                return True
        except (TimeoutException, NoSuchElementException):
            continue
    logging.warning(f"No PDF button found for link {idx}. Skipping.")
    return False


def process_link(driver, link, idx):
    """Processes a single link by attempting to download a PDF from it."""
    if not link.strip():
        logging.warning(f"Skipping empty link at index {idx}")
        return False
    try:
        logging.info(f"Processing link {idx}: {link}")
        driver.get(link)
        time.sleep(5)  # Wait for page to load
        return download_pdf(driver, link, idx)
    except WebDriverException as e:
        logging.error(f"WebDriver error processing link {idx}: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error processing link {idx}: {str(e)}")
    return False


def create_driver_pool(num_instances):
    """Creates a pool of WebDriver instances."""
    for _ in range(num_instances):
        driver = initialize_driver()
        if driver:
            driver_queue.put(driver)


def process_link_with_own_driver(link_idx_tuple):
    """Processes a link using a WebDriver instance from the pool."""
    idx, link = link_idx_tuple
    driver = driver_queue.get()
    try:
        if not process_link(driver, link, idx):
            logging.warning(f"Failed to process link {idx}. Moving to next link.")
    finally:
        driver_queue.put(driver)


def rename_files_remove_splitted():
    """Renames downloaded files to remove '_splitted' from their names."""
    for file_name in os.listdir(DOWNLOAD_DIR):
        if "_splitted" in file_name:
            new_file_name = file_name.replace("_splitted-", "")
            os.rename(
                os.path.join(DOWNLOAD_DIR, file_name),
                os.path.join(DOWNLOAD_DIR, new_file_name),
            )
            logging.info(f"Renamed {file_name} to {new_file_name}")


def main():
    """Main function to orchestrate the download process."""
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
    create_driver_pool(NUM_PROCESSES)
    with open(LINKS_FILE, "r") as file:
        links = [link.strip() for link in file.readlines() if link.strip()]
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_PROCESSES) as executor:
        list(executor.map(process_link_with_own_driver, enumerate(links, start=1)))
    logging.info("Download process completed.")
    rename_files_remove_splitted()
    while not driver_queue.empty():
        driver = driver_queue.get()
        driver.quit()


if __name__ == "__main__":
    main()
