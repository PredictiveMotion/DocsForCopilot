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

# Set up logging
logging.basicConfig(
    filename="pdf_download.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Initialize a queue for WebDriver instances
driver_queue = Queue()

# Adjustable constant for the number of Chrome processes
NUM_PROCESSES = 5


def get_os_specific_paths():
    if platform.system() == "Linux":
        chrome_driver_path = "./chrome_linux/chromedriver"  # Adjust this path
        binary_location = os.path.abspath(
            "chrome_linux/chrome-linux64/chrome"
        )  # Adjust if necessary
    elif platform.system() == "Windows":
        chrome_driver_path = (
            "c:/development/samples/pdfToMarkdown/chromedriver.exe"  # Adjust this path
        )
        binary_location = None  # Not needed for Windows in this setup
    else:
        raise NotImplementedError("This script only supports Linux and Windows")
    return chrome_driver_path, binary_location


def initialize_driver():
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

    prefs = {
        "download.default_directory": os.path.abspath("downloaded_pdfs"),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
    }
    options.add_experimental_option("prefs", prefs)

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
    try:
        for selector in [
            "//button[@data-bi-name='download-pdf']",
            "//a[contains(@href, '.pdf')]",
            "//button[contains(text(), 'Download PDF')]",
            "//a[contains(text(), 'Download PDF')]",
        ]:
            try:
                pdf_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                pdf_button.click()
                logging.info(
                    f"PDF button found and clicked for link {idx} using selector: {selector}"
                )

                # Wait for download to complete
                time.sleep(10)  # Adjust this time based on typical download duration

                # Check if PDF was downloaded
                download_dir = os.path.abspath("downloaded_pdfs")
                downloaded_files = os.listdir(download_dir)
                pdf_files = [f for f in downloaded_files if f.endswith(".pdf")]

                if pdf_files:
                    logging.info(f"Downloaded PDF for link {idx}")
                    return True
                else:
                    logging.warning(
                        f"No PDF file found in download directory for link {idx}"
                    )
                    return False
            except (TimeoutException, NoSuchElementException):
                continue

        logging.warning(f"No PDF button found for link {idx}. Skipping.")
        return False
    except Exception as e:
        logging.error(f"Error downloading PDF for link {idx}: {str(e)}")
        return False


def process_link(driver, link, idx):
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
    for _ in range(num_instances):
        driver = initialize_driver()
        if driver:
            driver_queue.put(driver)


def process_link_with_own_driver(link_idx_tuple):
    idx, link = link_idx_tuple
    driver = driver_queue.get()  # Borrow a WebDriver instance from the pool
    try:
        success = process_link(driver, link, idx)
        if not success:
            logging.warning(f"Failed to process link {idx}. Moving to next link.")
    finally:
        driver_queue.put(driver)  # Return the WebDriver instance to the pool


def rename_files_remove_splitted(download_dir):
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


def main():
    download_dir = "downloaded_pdfs"
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    create_driver_pool(NUM_PROCESSES)  # Initialize the WebDriver pool

    with open("framework452_links.txt", "r") as file:
        links = [link.strip() for link in file.readlines() if link.strip()]

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_PROCESSES) as executor:
        list(executor.map(process_link_with_own_driver, enumerate(links, start=1)))

    logging.info("Download process completed.")
    rename_files_remove_splitted(download_dir)

    # Cleanup: Quit all WebDriver instances in the pool
    while not driver_queue.empty():
        driver = driver_queue.get()
        driver.quit()


if __name__ == "__main__":
    main()
