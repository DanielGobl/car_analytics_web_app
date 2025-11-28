"""
Web scraper for autobazar.eu car listings
Scrapes car data and saves to CSV file
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import re
from typing import List, Dict, Optional


class AutobazarScraper:
    """Scraper for autobazar.eu car listings"""

    def __init__(self, base_url: str = "https://www.autobazar.eu"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        })
        self.listings = []

    def build_search_url(self, **params) -> str:
        """
        Build search URL with parameters

        Args:
            brand: Car brand (e.g., 'BMW', 'Audi')
            model: Car model
            year_from: Minimum year
            year_to: Maximum year
            price_from: Minimum price
            price_to: Maximum price
            engine: Engine type (petrol, diesel, electric, hybrid)
            transmission: Transmission type (manual, automatic)
            mileage_to: Maximum mileage
        """
        # Base search URL - adjust based on actual site structure
        search_url = f"{self.base_url}/search"

        # This will need to be adjusted based on actual site URL structure
        query_params = []

        param_mapping = {
            'brand': 'brand',
            'model': 'model',
            'year_from': 'yearFrom',
            'year_to': 'yearTo',
            'price_from': 'priceFrom',
            'price_to': 'priceTo',
            'engine': 'fuel',
            'transmission': 'transmission',
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

        # Remove currency symbols and spaces, extract numbers
        price_clean = re.sub(r'[^\d,.]', '', price_text)
        price_clean = price_clean.replace(',', '').replace(' ', '')

        try:
            return float(price_clean)
        except ValueError:
            return None

    def extract_number(self, text: str) -> Optional[int]:
        """Extract numeric value from text"""
        if not text:
            return None

        numbers = re.findall(r'\d+', text.replace(' ', ''))
        if numbers:
            return int(numbers[0])
        return None

    def parse_listing(self, listing_element) -> Optional[Dict]:
        """
        Parse individual car listing element

        NOTE: This structure will need to be adjusted based on actual HTML structure
        """
        try:
            # These selectors are placeholders and will need adjustment
            title = listing_element.find('h2', class_=re.compile('title|heading|name'))
            price = listing_element.find(class_=re.compile('price'))
            year = listing_element.find(class_=re.compile('year|rok'))
            mileage = listing_element.find(class_=re.compile('mileage|km|kilom'))
            engine = listing_element.find(class_=re.compile('engine|motor|fuel'))
            transmission = listing_element.find(class_=re.compile('transmission|prevodovka'))
            location = listing_element.find(class_=re.compile('location|lokalita'))
            link = listing_element.find('a', href=True)

            listing_data = {
                'title': title.text.strip() if title else None,
                'price': self.extract_price(price.text) if price else None,
                'price_text': price.text.strip() if price else None,
                'year': self.extract_number(year.text) if year else None,
                'mileage': self.extract_number(mileage.text) if mileage else None,
                'engine': engine.text.strip() if engine else None,
                'transmission': transmission.text.strip() if transmission else None,
                'location': location.text.strip() if location else None,
                'url': self.base_url + link['href'] if link and link.get('href') else None,
                'scraped_at': datetime.now().isoformat()
            }

            return listing_data

        except Exception as e:
            print(f"Error parsing listing: {e}")
            return None

    def scrape_page(self, url: str) -> List[Dict]:
        """Scrape a single page of listings"""
        try:
            print(f"Scraping: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # Find all listing elements - adjust selector based on actual site
            listings = soup.find_all(class_=re.compile('listing|car-item|vehicle|advert'))

            # Alternative: try finding by common container patterns
            if not listings:
                listings = soup.find_all('article')
            if not listings:
                listings = soup.find_all('div', class_=re.compile('item|card'))

            print(f"Found {len(listings)} listings on page")

            page_data = []
            for listing in listings:
                listing_data = self.parse_listing(listing)
                if listing_data and listing_data['title']:
                    page_data.append(listing_data)

            return page_data

        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return []

    def scrape_multiple_pages(self, base_search_url: str, max_pages: int = 5) -> List[Dict]:
        """Scrape multiple pages of listings"""
        all_data = []

        for page_num in range(1, max_pages + 1):
            # Adjust pagination URL pattern based on actual site
            page_url = f"{base_search_url}&page={page_num}"
            if '?' not in base_search_url:
                page_url = f"{base_search_url}?page={page_num}"

            page_data = self.scrape_page(page_url)

            if not page_data:
                print(f"No more listings found on page {page_num}")
                break

            all_data.extend(page_data)

            # Be respectful - add delay between requests
            time.sleep(2)

        return all_data

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
        print(f"Saved {len(data)} listings to {filename}")

        # Print summary statistics
        print("\n=== Scraping Summary ===")
        print(f"Total listings: {len(data)}")
        if 'price' in df.columns:
            print(f"Average price: €{df['price'].mean():.2f}")
            print(f"Price range: €{df['price'].min():.2f} - €{df['price'].max():.2f}")
        if 'year' in df.columns:
            print(f"Year range: {df['year'].min()} - {df['year'].max()}")

    def run(self, search_params: Dict = None, max_pages: int = 5, output_file: str = None):
        """
        Run the scraper with given parameters

        Args:
            search_params: Dictionary of search parameters
            max_pages: Maximum number of pages to scrape
            output_file: Output CSV filename
        """
        print("Starting autobazar.eu scraper...")
        print(f"Search parameters: {search_params}")

        if search_params:
            search_url = self.build_search_url(**search_params)
        else:
            search_url = f"{self.base_url}/search"

        data = self.scrape_multiple_pages(search_url, max_pages)

        if data:
            self.save_to_csv(data, output_file)
            return data
        else:
            print("No data scraped. Please check the site structure and update selectors.")
            return []


def main():
    """Example usage"""
    scraper = AutobazarScraper()

    # Example 1: Scrape all listings (first 5 pages)
    # scraper.run(max_pages=5)

    # Example 2: Scrape with specific parameters
    search_params = {
        'brand': 'BMW',
        # 'model': '3-Series',
        'year_from': 2018,
        'price_to': 30000,
        # 'engine': 'diesel',
        # 'transmission': 'automatic'
    }

    scraper.run(search_params=search_params, max_pages=3, output_file='bmw_listings.csv')


if __name__ == "__main__":
    main()
