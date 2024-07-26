"""Functions for downloading PDFs using Selenium WebDriver."""

import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

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

def wait_for_download(pdf_path, crdownload_path, idx, pdf_filename):
    """Wait for the PDF download to complete."""
    max_wait_time = 300  # 5 minutes
    start_time = time.time()
    while time.time() - start_time < max_wait_time:
        if check_download_complete(pdf_path, idx, pdf_filename):
            return True
        if os.path.exists(crdownload_path):
            time.sleep(2)
        else:
            time.sleep(5)
            break
    return cleanup_and_check(pdf_path, crdownload_path, idx, pdf_filename)

def download_pdf(driver, link, idx, download_dir):
    """Attempt to download a PDF from the given link."""
    pdf_filename = link.split("/")[-1].split("?")[0] + ".pdf"
    pdf_path = os.path.join(download_dir, pdf_filename)
    crdownload_path = os.path.join(download_dir, f"{pdf_filename}.crdownload")

    if os.path.exists(pdf_path):
        logging.info(f"PDF already exists for link {idx}: {pdf_filename}")
        return True

    if click_pdf_button(driver, idx):
        return wait_for_download(pdf_path, crdownload_path, idx, pdf_filename)

    logging.warning(f"No PDF button found for link {idx}. Skipping.")
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
