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
import time

# Replace with your ChromeDriver path
chrome_driver_path = "c:/development/samples/pdfToMarkdown/chromedriver.exe"

# Set up Chrome options
options = Options()
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

# Initialize WebDriver
service = Service(executable_path=chrome_driver_path)

# Define the URL
url = "https://learn.microsoft.com/en-us/dotnet/api/?view=netframework-4.5.2&preserve-view=true"

# Use a context manager for the WebDriver
with webdriver.Chrome(service=service, options=options) as driver:
    try:
        # Visit the webpage
        driver.get(url)
        
        # Wait for the page to load (up to 10 seconds)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href]"))
        )

        # Extract all the links
        links = driver.find_elements(By.XPATH, "//a[@href]")

        # Filter the links
        desired_links = [
            link.get_attribute("href")
            for link in links
            if link.get_attribute("href").startswith("https://learn.microsoft.com/en-us/dotnet/api/")
            and "view=netframework-4.5.2" in link.get_attribute("href")
        ]

        # Print the extracted links and save them to a file
        output_file = "framework452_links.txt"
        with open(output_file, "w", encoding="utf-8") as file:
            for idx, link in enumerate(desired_links, start=1):
                print(f"{idx}: {link}")
                file.write(link + "\n")

        print(f"Links have been saved to {output_file}")

    except TimeoutException:
        print("Timed out waiting for page to load")
    except Exception as e:
        print(f"An error occurred: {e}")
