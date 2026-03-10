# Houzz Interior Designers Scraper

A Scrapy-based web scraper that collects interior designer business data from [Houzz.com](https://www.houzz.com), organized state by state across all 50 US states.

## Features

- Scrapes interior designer profiles across all 50 US states
- Saves data per state into individual CSV files (real-time, appended as scraped)
- Resumes from where it left off if interrupted (progress tracking via `progress.json`)
- Supports filtering by specific states or limiting the number of states/cities
- Rotating user agents and adaptive throttling to reduce blocking

## Data Collected

Each company record includes:

| Field | Description |
|---|---|
| `name` | Designer/company name |
| `business_name` | Registered business name |
| `phone` | Contact phone number |
| `website` | Business website URL |
| `address` | Physical address |
| `city` | City |
| `state` | State |
| `rating` | Houzz rating |
| `reviews` | Number of reviews |
| `profile_url` | Houzz profile URL |

## Project Structure

```
houzz_scrapy/
├── houzz_scrapy/
│   ├── spiders/
│   │   └── houzz_spider.py   # Main spider
│   ├── items.py
│   ├── middlewares.py        # Rotating user agent middleware
│   ├── pipelines.py
│   └── settings.py
├── state_data/               # Output directory (created on run)
│   ├── houzz_alabama.csv
│   ├── houzz_alaska.csv
│   ├── ...
│   └── progress.json         # Tracks completed states
├── run_spider.py             # Convenience runner script
└── scrapy.cfg
```

## Requirements

- Python 3.8+
- Scrapy
- BeautifulSoup4

Install dependencies:

```bash
pip install scrapy beautifulsoup4
```

## Usage

### Run with the convenience script

```bash
# Scrape all states
python run_spider.py

# Limit to 5 states
python run_spider.py --states 5

# Limit to 2 states, 3 cities each
python run_spider.py --states 2 --cities 3

# Scrape specific states only
python run_spider.py --state-names Washington "New York" California

# Custom output directory
python run_spider.py --output my_data

# Adjust log verbosity
python run_spider.py --log-level DEBUG
```

### Run directly with Scrapy

```bash
scrapy crawl houzz

# With arguments
scrapy crawl houzz -a max_states=3 -a max_cities=5 -a output_dir=state_data
scrapy crawl houzz -a state_names="Washington,New York,Texas"
```

## Output

Each state gets its own CSV file inside the output directory:

```
state_data/               # default output_dir
├── houzz_alabama.csv
├── houzz_new_york.csv
├── houzz_texas.csv
├── ...
├── houzz_companies.csv   # combined feed output
└── progress.json
```

The scraper saves records in real-time — data is written to CSV as each company is scraped, so partial results are preserved even if the run is interrupted.

## Resuming Interrupted Runs

If the spider is stopped mid-run, simply run it again with the same `--output` directory. It will automatically skip states that have already been completed (tracked in `progress.json`) and continue from where it left off.

## Settings

Key settings in `houzz_scrapy/settings.py`:

| Setting | Value | Description |
|---|---|---|
| `CONCURRENT_REQUESTS` | 8 | Parallel requests |
| `DOWNLOAD_DELAY` | 0.5s | Delay between requests |
| `AUTOTHROTTLE_ENABLED` | True | Adaptive throttling |
| `RETRY_TIMES` | 3 | Retries on failure |
| `ROBOTSTXT_OBEY` | False | Ignores robots.txt |
