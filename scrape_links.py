from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

# Replace with your ChromeDriver path
chrome_driver_path = "c:/development/samples/pdfToMarkdown/chromedriver.exe"

# Set up Chrome options
options = Options()
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

# Initialize WebDriver
service = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

# Define the URL
url = "https://learn.microsoft.com/en-us/dotnet/api/?view=netframework-4.5.2&preserve-view=true"

# Visit the webpage
driver.get(url)
time.sleep(2)  # Wait for the page to load

# Extract all the links
links = driver.find_elements(By.XPATH, "//a[@href]")

# Filter the links
desired_links = []
for link in links:
    href = link.get_attribute("href")
    if (
        href.startswith("https://learn.microsoft.com/en-us/dotnet/api/")
        and "view=netframework-4.5.2" in href
    ):
        desired_links.append(href)


# Print the extracted links and save them to a file
with open("framework452_links2.txt", "w", encoding="utf-8") as file:
    for idx, link in enumerate(desired_links, start=1):
        print(f"{idx}: {link}")
        file.write(link + "\n")

# Close the WebDriver
driver.quit()
