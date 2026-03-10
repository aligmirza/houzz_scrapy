# Scrapy settings for houzz_scrapy project

BOT_NAME = "houzz_scrapy"

SPIDER_MODULES = ["houzz_scrapy.spiders"]
NEWSPIDER_MODULE = "houzz_scrapy.spiders"

# Rotating User Agents List
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
]

# Default User Agent (will be rotated by middleware)
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Don't obey robots.txt for this scraper
ROBOTSTXT_OBEY = False

# Concurrency settings - faster
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 4
DOWNLOAD_DELAY = 0.5  # 0.5 second delay between requests

# Enable cookies
COOKIES_ENABLED = True

# Default request headers to look like a real browser
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# Enable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    "houzz_scrapy.middlewares.RotateUserAgentMiddleware": 400,
    "houzz_scrapy.middlewares.HouzzScrapyDownloaderMiddleware": 543,
}

# Enable AutoThrottle for adaptive delay
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.5
AUTOTHROTTLE_MAX_DELAY = 5
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0
AUTOTHROTTLE_DEBUG = False

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Handle 403 errors
HTTPERROR_ALLOWED_CODES = [403]

# Log level
LOG_LEVEL = 'INFO'

# Output settings - Default output file saved inside output_dir
FEEDS = {
    'state_data/houzz_companies.csv': {
        'format': 'csv',
        'overwrite': True,
        'fields': ['name', 'business_name', 'phone', 'website', 'address', 'rating', 'reviews', 'profile_url'],
    }
}

FEED_EXPORT_ENCODING = "utf-8"

# Request fingerprinter
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
