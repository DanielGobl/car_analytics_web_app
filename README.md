# Car Analytics Web App

Web application for price analytics of used cars from autobazar.eu

## Current Status

✅ Web scraping script with Selenium (Phase 1)

## Features

- **Dynamic Content Support**: Uses Selenium to handle React/JavaScript-rendered content
- **Flexible Search**: Filter by brand, model, year, price, fuel type, transmission, mileage
- **Auto-scrolling**: Loads more listings via infinite scroll
- **Robust Parsing**: Multiple CSS selectors for reliable data extraction
- **CSV Export**: Clean, structured data output with statistics

## Prerequisites

- Python 3.8+
- Chrome browser installed
- ChromeDriver (will be managed automatically by webdriver-manager)

## Setup

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Quick Start

```bash
python scraper.py
```

This will scrape BMW listings from 2018+ under €30,000 and save to `bmw_listings.csv`.

### Custom Search

Edit the `main()` function in `scraper.py`:

```python
scraper = AutobazarScraper(headless=True)  # Set False to see browser

search_params = {
    'category': 'osobne-vozidla',  # osobne-vozidla, suv-terenne-vozidla, motocykle
    'brand': 'audi',               # Brand (lowercase)
    'model': 'a4',                 # Model (lowercase with dashes, optional)
    'year_from': 2018,             # Minimum year
    'year_to': 2024,               # Maximum year
    'price_from': 5000,            # Minimum price in EUR
    'price_to': 30000,             # Maximum price in EUR
    'fuel': 'nafta',               # benzin, nafta, hybrid, elektro, lpg
    'transmission': 'automat',     # manual, automat
    'mileage_from': 0,             # Minimum mileage in km
    'mileage_to': 150000           # Maximum mileage in km
}

scraper.run(
    search_params=search_params,
    scroll_times=5,                # How many times to scroll (loads ~20 listings per scroll)
    output_file='audi_a4.csv'
)
```

### Scraping Without Filters

```python
scraper = AutobazarScraper(headless=True)
scraper.run(scroll_times=10, output_file='all_cars.csv')
```

## How It Works

1. **Selenium WebDriver** launches Chrome and navigates to autobazar.eu
2. **URL Builder** constructs search URL based on parameters
3. **Wait & Scroll** waits for React to render, then scrolls to trigger lazy loading
4. **Smart Parsing** tries multiple CSS selectors to extract data reliably
5. **CSV Export** saves structured data with summary statistics

## Output

The scraper saves data to CSV files with the following columns:

| Column | Description |
|--------|-------------|
| `title` | Car listing title/heading |
| `brand` | Car brand (if extracted) |
| `model` | Car model (if extracted) |
| `price` | Numeric price in EUR |
| `price_text` | Original price text |
| `year` | Manufacturing year |
| `mileage` | Mileage in km |
| `mileage_text` | Original mileage text |
| `engine` | Engine description |
| `engine_power` | Engine power in kW |
| `fuel` | Fuel type (Benzín, Nafta, Hybrid, etc.) |
| `transmission` | Transmission type |
| `location` | Seller location |
| `url` | Full URL to listing |
| `scraped_at` | ISO timestamp |

### Example Output

```
Total listings: 47
Average price: €18,234.50
Price range: €5,900.00 - €29,500.00
Year range: 2018 - 2024
Average mileage: 87,432 km
```

## Roadmap

- [ ] MySQL database integration
- [ ] Web interface for search
- [ ] Price analytics & charts
- [ ] Price trend analysis
- [ ] Overpriced/underpriced detection
