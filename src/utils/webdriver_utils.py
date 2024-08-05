"""Utility functions for managing WebDriver instances."""

import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from config import CHROME_DRIVER_PATH

def initialize_driver(download_dir):
    """Initialize and configure a Chrome WebDriver instance."""
    options = Options()
#    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")

    # add log entry for download_dir
    logging.info(f"initialize driver, Download directory: {download_dir}")


    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        # "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
    }
    options.add_experimental_option("prefs", prefs)

    service = Service(executable_path=CHROME_DRIVER_PATH)

    try:
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        logging.info("WebDriver initialized successfully")
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize WebDriver: {str(e)}")
        return None

def create_driver_pool(num_instances, download_dir, driver_queue, create_driver_func=None):
    """Create a pool of WebDriver instances."""
    for _ in range(num_instances):
        if create_driver_func:
            driver = create_driver_func(download_dir)
        else:
            driver = initialize_driver(download_dir)
        if driver:
            driver_queue.put(driver)

def cleanup_driver_pool(driver_queue):
    """Quit all WebDriver instances in the pool."""
    while not driver_queue.empty():
        driver = driver_queue.get()
        driver.quit()
