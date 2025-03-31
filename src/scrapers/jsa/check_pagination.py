"""Script to check pagination structure on JSA website."""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

def setup_driver():
    """Set up Chrome WebDriver with headless options."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def main():
    url = "https://jewelerssecurity.org/category/crime-news/crimes/"
    driver = setup_driver()
    
    try:
        print(f"Fetching {url}...")
        driver.get(url)
        
        # Wait for content to load
        time.sleep(5)
        
        # Get page source after JavaScript execution
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find navigation elements
        nav = soup.find('nav', class_='navigation')
        if nav:
            print("Found navigation element:")
            print(nav.prettify())
        else:
            print("No navigation element found")
            
        # Find any elements with page-numbers class
        page_numbers = soup.find_all(class_='page-numbers')
        if page_numbers:
            print("\nFound page number elements:")
            for elem in page_numbers:
                print("\n", elem.prettify())
        else:
            print("\nNo page number elements found")
            
        # Try finding any elements that look like pagination
        print("\nSearching for other potential pagination elements:")
        for elem in soup.find_all(['div', 'nav', 'ul']):
            if any(word in str(elem.get('class', [])) for word in ['pag', 'nav']):
                print("\nPotential pagination element:")
                print(elem.prettify())
                
    finally:
        driver.quit()

if __name__ == "__main__":
    main() 