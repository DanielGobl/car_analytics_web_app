"""
Web scraper for autobazar.eu car listings
Uses Selenium to handle dynamic React/JavaScript content
Scrapes car data and saves to CSV file
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
from datetime import datetime
import time
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin


class AutobazarScraper:
    """Scraper for autobazar.eu car listings using Selenium"""

    def __init__(self, headless: bool = True, base_url: str = "https://www.autobazar.eu"):
        self.base_url = base_url
        self.headless = headless
        self.driver = None
        self.listings = []

    def setup_driver(self):
        """Initialize Selenium WebDriver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)

    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()

    def build_search_url(self, category: str = "osobne-vozidla", **params) -> str:
        """
        Build search URL with parameters

        Args:
            category: Vehicle category (osobne-vozidla, suv-terenne-vozidla, motocykle)
            brand: Car brand (lowercase, e.g., 'bmw', 'audi', 'volkswagen')
            model: Car model (lowercase with dashes, e.g., '3-serie', 'a4')
            year_from: Minimum year
            year_to: Maximum year
            price_from: Minimum price in EUR
            price_to: Maximum price in EUR
            fuel: Fuel type (benzin, nafta, hybrid, elektro, lpg)
            transmission: Transmission type (manual, automat)
            mileage_from: Minimum mileage in km
            mileage_to: Maximum mileage in km
        """
        # Base URL structure: /vysledky/[category]/[brand]/[model]/
        path_parts = ["vysledky", category]

        if params.get('brand'):
            path_parts.append(params['brand'].lower())
            if params.get('model'):
                path_parts.append(params['model'].lower())

        search_url = f"{self.base_url}/{'/'.join(path_parts)}/"

        # Query parameters for filters
        query_params = []

        param_mapping = {
            'year_from': 'yearFrom',
            'year_to': 'yearTo',
            'price_from': 'priceFrom',
            'price_to': 'priceTo',
            'fuel': 'fuel',
            'transmission': 'transmission',
            'mileage_from': 'mileageFrom',
            'mileage_to': 'mileageTo'
        }

        for key, value in params.items():
            if value and key in param_mapping:
                query_params.append(f"{param_mapping[key]}={value}")

        if query_params:
            search_url += "?" + "&".join(query_params)

        return search_url

    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price from text"""
        if not price_text:
            return None

        # Remove currency symbols, spaces, and extract numbers
        price_clean = re.sub(r'[^\d]', '', price_text)

        try:
            return float(price_clean)
        except ValueError:
            return None

    def extract_number(self, text: str) -> Optional[int]:
        """Extract numeric value from text"""
        if not text:
            return None

        numbers = re.findall(r'\d+', text.replace(' ', '').replace('\xa0', ''))
        if numbers:
            return int(''.join(numbers))
        return None

    def wait_for_listings(self, timeout: int = 15):
        """Wait for listings to load on the page"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid*='listing'], article, .car-item, .vehicle-item"))
            )
            # Additional wait for content to fully render
            time.sleep(2)
            return True
        except TimeoutException:
            print("Timeout waiting for listings to load")
            return False

    def scroll_to_load_more(self, num_scrolls: int = 3):
        """Scroll down to trigger lazy loading of more listings"""
        for i in range(num_scrolls):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        # Scroll back to top
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

    def parse_listing_element(self, element) -> Optional[Dict]:
        """Parse individual car listing element"""
        try:
            listing_data = {
                'title': None,
                'brand': None,
                'model': None,
                'price': None,
                'price_text': None,
                'year': None,
                'mileage': None,
                'mileage_text': None,
                'engine': None,
                'engine_power': None,
                'fuel': None,
                'transmission': None,
                'location': None,
                'url': None,
                'scraped_at': datetime.now().isoformat()
            }

            # Try to find title/heading
            try:
                title_elem = element.find_element(By.CSS_SELECTOR, "h2, h3, [class*='title'], [class*='heading'], a")
                listing_data['title'] = title_elem.text.strip()
            except NoSuchElementException:
                pass

            # Try to find price
            try:
                price_elem = element.find_element(By.CSS_SELECTOR, "[class*='price'], [class*='cena']")
                price_text = price_elem.text.strip()
                listing_data['price_text'] = price_text
                listing_data['price'] = self.extract_price(price_text)
            except NoSuchElementException:
                pass

            # Try to find year
            try:
                year_elem = element.find_element(By.CSS_SELECTOR, "[class*='year'], [class*='rok']")
                listing_data['year'] = self.extract_number(year_elem.text)
            except NoSuchElementException:
                # Try to extract from title
                if listing_data['title']:
                    year_match = re.search(r'\b(19|20)\d{2}\b', listing_data['title'])
                    if year_match:
                        listing_data['year'] = int(year_match.group())

            # Try to find mileage
            try:
                mileage_elem = element.find_element(By.CSS_SELECTOR, "[class*='mileage'], [class*='km'], [class*='kilom']")
                mileage_text = mileage_elem.text.strip()
                listing_data['mileage_text'] = mileage_text
                listing_data['mileage'] = self.extract_number(mileage_text)
            except NoSuchElementException:
                pass

            # Try to find fuel type
            try:
                fuel_elem = element.find_element(By.CSS_SELECTOR, "[class*='fuel'], [class*='palivo']")
                listing_data['fuel'] = fuel_elem.text.strip()
            except NoSuchElementException:
                pass

            # Try to find engine info
            try:
                engine_elem = element.find_element(By.CSS_SELECTOR, "[class*='engine'], [class*='motor']")
                engine_text = engine_elem.text.strip()
                listing_data['engine'] = engine_text
                # Try to extract power in kW
                power_match = re.search(r'(\d+)\s*kW', engine_text)
                if power_match:
                    listing_data['engine_power'] = int(power_match.group(1))
            except NoSuchElementException:
                pass

            # Try to find transmission
            try:
                trans_elem = element.find_element(By.CSS_SELECTOR, "[class*='transmission'], [class*='prevodovka']")
                listing_data['transmission'] = trans_elem.text.strip()
            except NoSuchElementException:
                pass

            # Try to find location
            try:
                loc_elem = element.find_element(By.CSS_SELECTOR, "[class*='location'], [class*='lokalita'], [class*='mesto']")
                listing_data['location'] = loc_elem.text.strip()
            except NoSuchElementException:
                pass

            # Try to find URL
            try:
                link_elem = element.find_element(By.CSS_SELECTOR, "a[href]")
                href = link_elem.get_attribute('href')
                if href:
                    listing_data['url'] = href if href.startswith('http') else urljoin(self.base_url, href)
            except NoSuchElementException:
                pass

            # Only return if we got at least a title or price
            if listing_data['title'] or listing_data['price']:
                return listing_data

            return None

        except Exception as e:
            print(f"Error parsing listing element: {e}")
            return None

    def scrape_page(self, url: str, scroll_times: int = 3) -> List[Dict]:
        """Scrape a single page of listings"""
        print(f"\nScraping: {url}")

        try:
            self.driver.get(url)

            # Wait for listings to load
            if not self.wait_for_listings():
                print("No listings found on page")
                return []

            # Scroll to load more content
            if scroll_times > 0:
                print(f"Scrolling {scroll_times} times to load more listings...")
                self.scroll_to_load_more(scroll_times)

            # Find all listing elements - try multiple selectors
            listings = []
            selectors = [
                "[data-testid*='listing']",
                "[data-testid*='advert']",
                "article",
                "[class*='car-item']",
                "[class*='vehicle-item']",
                "[class*='listing']",
                "[class*='advert-item']"
            ]

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements and len(elements) > listings.__len__():
                        listings = elements
                        print(f"Found {len(listings)} elements using selector: {selector}")
                except:
                    continue

            if not listings:
                print("No listing elements found with any selector")
                return []

            print(f"Parsing {len(listings)} listings...")
            page_data = []

            for idx, listing_elem in enumerate(listings, 1):
                listing_data = self.parse_listing_element(listing_elem)
                if listing_data:
                    page_data.append(listing_data)
                    if idx % 10 == 0:
                        print(f"  Parsed {idx}/{len(listings)} listings...")

            print(f"Successfully extracted {len(page_data)} listings")
            return page_data

        except Exception as e:
            print(f"Error scraping page: {e}")
            return []

    def save_to_csv(self, data: List[Dict], filename: str = None):
        """Save scraped data to CSV file"""
        if not data:
            print("No data to save")
            return

        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"car_listings_{timestamp}.csv"

        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"\n✓ Saved {len(data)} listings to {filename}")

        # Print summary statistics
        print("\n=== Scraping Summary ===")
        print(f"Total listings: {len(data)}")

        if 'price' in df.columns and df['price'].notna().any():
            valid_prices = df['price'].dropna()
            print(f"Average price: €{valid_prices.mean():,.2f}")
            print(f"Price range: €{valid_prices.min():,.2f} - €{valid_prices.max():,.2f}")

        if 'year' in df.columns and df['year'].notna().any():
            valid_years = df['year'].dropna()
            print(f"Year range: {int(valid_years.min())} - {int(valid_years.max())}")

        if 'mileage' in df.columns and df['mileage'].notna().any():
            valid_mileage = df['mileage'].dropna()
            print(f"Average mileage: {valid_mileage.mean():,.0f} km")

    def run(self, search_params: Dict = None, scroll_times: int = 3, output_file: str = None):
        """
        Run the scraper with given parameters

        Args:
            search_params: Dictionary of search parameters
            scroll_times: Number of times to scroll for lazy loading (0 to disable)
            output_file: Output CSV filename
        """
        print("="*60)
        print("Starting autobazar.eu scraper with Selenium")
        print("="*60)

        if search_params:
            print(f"Search parameters: {search_params}")

        try:
            # Setup browser
            print("\nInitializing Chrome driver...")
            self.setup_driver()

            # Build search URL
            if search_params:
                search_url = self.build_search_url(**search_params)
            else:
                search_url = f"{self.base_url}/vysledky/osobne-vozidla/"

            # Scrape the page
            data = self.scrape_page(search_url, scroll_times=scroll_times)

            # Save to CSV
            if data:
                self.save_to_csv(data, output_file)
                return data
            else:
                print("\n⚠ No data scraped. The page structure might have changed.")
                print("Please inspect the page manually and update the selectors.")
                return []

        except Exception as e:
            print(f"\n❌ Error during scraping: {e}")
            return []

        finally:
            # Clean up
            print("\nClosing browser...")
            self.close_driver()


def main():
    """Example usage"""

    # Example 1: Scrape BMW listings
    scraper = AutobazarScraper(headless=True)

    search_params = {
        'category': 'osobne-vozidla',  # Personal vehicles
        'brand': 'bmw',
        # 'model': '3-serie',
        'year_from': 2018,
        'price_to': 30000,
        # 'fuel': 'nafta',  # diesel
        # 'transmission': 'automat',
    }

    scraper.run(
        search_params=search_params,
        scroll_times=3,  # Scroll 3 times to load more listings
        output_file='bmw_listings.csv'
    )

    # Example 2: Scrape all cars (no filters)
    # scraper = AutobazarScraper(headless=True)
    # scraper.run(scroll_times=5, output_file='all_cars.csv')


if __name__ == "__main__":
    main()
