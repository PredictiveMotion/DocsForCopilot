"""Scrape links from Microsoft .NET API documentation using Selenium WebDriver."""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def setup_driver(chrome_driver_path):
    """Set up and return the Chrome WebDriver with custom options."""
    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--log-level=3")  # Only show fatal errors
    options.add_argument("--silent")
    service = Service(executable_path=chrome_driver_path)
    return webdriver.Chrome(service=service, options=options)

def get_links(driver, url, view):
    """Navigate to the URL and extract relevant links matching the specified view."""
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//a[@href]")))
    links = driver.find_elements(By.XPATH, "//a[@href]")
    return [
        link.get_attribute("href")
        for link in links
        if link.get_attribute("href").startswith("https://learn.microsoft.com/en-us/dotnet/api/")
        and f"view={view}" in link.get_attribute("href")
    ]

def save_links(links, output_file):
    """Save the extracted links to a file and print them to console."""
    with open(output_file, "w", encoding="utf-8") as file:
        for idx, link in enumerate(links, start=1):
            print(f"{idx}: {link}")
            file.write(link + "\n")
    print(f"Links have been saved to {output_file}")

def read_urls_from_file(file_path):
    """Read URLs from the specified file, ignoring empty lines."""
    with open(file_path, "r") as file:
        return [line.strip() for line in file if line.strip()]

def select_url(urls):
    """Prompt the user to select a URL from the list and return the chosen URL."""
    print("Available URLs:")
    for idx, url in enumerate(urls, start=1):
        print(f"{idx}. {url}")
    
    while True:
        try:
            choice = int(input("Enter the number of the URL you want to scrape: "))
            if 1 <= choice <= len(urls):
                return urls[choice - 1]
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def main():
    """Main function to set up the driver, scrape links, and save them to a file."""
    chrome_driver_path = "chrome/chrome_windows/chromedriver.exe"
    urls_file = "../data/links_to_scrape.txt"
    
    urls = read_urls_from_file(urls_file)
    url_to_parse = select_url(urls)
    
    view = url_to_parse.split('view=')[-1].split('&')[0]
    output_file = f"../data/scraped_links_{view}.txt"

    try:
        with setup_driver(chrome_driver_path) as driver:
            links = get_links(driver, url_to_parse, view)
            if links:
                save_links(links, output_file)
                print(f"{len(links)} links have been saved to {output_file}")
            else:
                print(f"No links found for the view: {view}")
    except TimeoutException:
        print("Timed out waiting for page to load")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
