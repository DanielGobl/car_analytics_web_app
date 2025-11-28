# Car Analytics Web App

Web application for price analytics of used cars from autobazar.eu

## Current Status

✅ Web scraping script (Phase 1)

## Setup

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Scraping

```bash
python scraper.py
```

### Advanced Usage

Edit the `main()` function in `scraper.py` to customize search parameters:

```python
search_params = {
    'brand': 'BMW',           # Car brand
    'model': '3-Series',      # Car model (optional)
    'year_from': 2018,        # Minimum year
    'year_to': 2024,          # Maximum year
    'price_from': 5000,       # Minimum price in EUR
    'price_to': 30000,        # Maximum price in EUR
    'engine': 'diesel',       # Engine type: petrol, diesel, electric, hybrid
    'transmission': 'automatic', # manual or automatic
    'mileage_to': 150000      # Maximum mileage in km
}

scraper.run(search_params=search_params, max_pages=5, output_file='my_search.csv')
```

## Important Notes

⚠️ **The scraper needs calibration for autobazar.eu's actual HTML structure**

Before first use, you should:

1. Visit autobazar.eu manually and inspect the HTML structure
2. Update the CSS selectors in `parse_listing()` method to match actual class names
3. Update the URL parameter mapping in `build_search_url()` to match the site's query format
4. Test with `max_pages=1` first to verify it works

## Output

The scraper saves data to CSV files with the following columns:
- `title`: Car listing title
- `price`: Numeric price value
- `price_text`: Original price text
- `year`: Manufacturing year
- `mileage`: Mileage in km
- `engine`: Engine/fuel type
- `transmission`: Transmission type
- `location`: Seller location
- `url`: Link to listing
- `scraped_at`: Timestamp when scraped

## Features

- ✅ Configurable search parameters
- ✅ Multi-page scraping
- ✅ CSV export
- ✅ Automatic price/number extraction
- ✅ Polite scraping with delays
- ✅ Summary statistics

## Roadmap

- [ ] MySQL database integration
- [ ] Web interface for search
- [ ] Price analytics & charts
- [ ] Price trend analysis
- [ ] Overpriced/underpriced detection
