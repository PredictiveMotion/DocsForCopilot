"""
Scrape links from the Microsoft .NET Framework 4.5.2 API documentation.

This script uses Selenium WebDriver to navigate to the .NET Framework 4.5.2 API
documentation page, extract all relevant links, and save them to a text file.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def setup_driver(chrome_driver_path):
    """Set up and return the Chrome WebDriver."""
    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    service = Service(executable_path=chrome_driver_path)
    return webdriver.Chrome(service=service, options=options)

def get_links(driver, url):
    """Navigate to the URL and extract relevant links."""
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[@href]")))
    links = driver.find_elements(By.XPATH, "//a[@href]")
    return [
        link.get_attribute("href")
        for link in links
        if link.get_attribute("href").startswith("https://learn.microsoft.com/en-us/dotnet/api/")
        and "view=netframework-4.5.2" in link.get_attribute("href")
    ]

def save_links(links, output_file):
    """Save the extracted links to a file."""
    with open(output_file, "w", encoding="utf-8") as file:
        for idx, link in enumerate(links, start=1):
            print(f"{idx}: {link}")
            file.write(link + "\n")
    print(f"Links have been saved to {output_file}")

def main():
    chrome_driver_path = "c:/development/samples/pdfToMarkdown/chromedriver.exe"
    url_to_parse = "https://learn.microsoft.com/en-us/dotnet/api/?view=netframework-4.5.2&preserve-view=true"
    output_file = "framework452_links.txt"

    try:
        with setup_driver(chrome_driver_path) as driver:
            links = get_links(driver, url_to_parse)
            save_links(links, output_file)
    except TimeoutException:
        print("Timed out waiting for page to load")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
