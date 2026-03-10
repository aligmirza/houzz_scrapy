"""
Houzz Interior Designers Scraper - State-wise Edition
Scrapes one state at a time, saves each state to separate CSV file
"""
import re
import os
import json
import time
import scrapy
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime


class HouzzSpider(scrapy.Spider):
    name = "houzz"
    base_url = "https://www.houzz.com"

    # Start from the professionals browse page
    start_urls = ["https://www.houzz.com/professionals/interior-designer"]

    # All US States
    US_STATES = [
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
        "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
        "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
        "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
        "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
        "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma",
        "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
        "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
        "West Virginia", "Wisconsin", "Wyoming"
    ]

    custom_settings = {
        'FEEDS': {},  # We'll handle CSV output manually per state
        'LOG_LEVEL': 'INFO',
    }

    def __init__(self, max_states=None, max_cities=None, output_dir='state_data',
                 state_names=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_states = int(max_states) if max_states else None
        self.max_cities = int(max_cities) if max_cities else None
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Parse state names whitelist
        if state_names:
            self.state_names = [name.strip().lower() for name in state_names.split(',')]
        else:
            self.state_names = None

        self.start_time = time.time()
        self.seen_profiles = set()

        # State tracking
        self.all_states = []
        self.current_state = None
        self.current_state_companies = []
        self.state_queue = []
        self.completed_states = set()
        self.state_stats = {}

        # Progress file
        self.progress_file = self.output_dir / "progress.json"
        self._load_progress()

    def _load_progress(self):
        """Load progress from previous runs"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    self.completed_states = set(data.get('completed_states', []))
                    self.state_stats = data.get('state_stats', {})
                    self.logger.info(f"Loaded progress: {len(self.completed_states)} states completed")
                    if self.completed_states:
                        self.logger.info(f"Completed: {', '.join(sorted(self.completed_states))}")
            except Exception as e:
                self.logger.warning(f"Could not load progress: {e}")

    def _save_progress(self):
        """Save progress to file"""
        with open(self.progress_file, 'w') as f:
            json.dump({
                'completed_states': list(self.completed_states),
                'state_stats': self.state_stats,
                'total_companies': sum(s.get('companies', 0) for s in self.state_stats.values()),
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)

    def _get_state_csv_path(self, state_name):
        """Get CSV file path for a state"""
        safe_name = state_name.lower().replace(' ', '_')
        return self.output_dir / f"houzz_{safe_name}.csv"

    def _save_state_to_csv(self, state_name, companies):
        """Save companies to state-specific CSV (full write)"""
        if not companies:
            return

        csv_path = self._get_state_csv_path(state_name)
        fieldnames = ['name', 'business_name', 'phone', 'website', 'address',
                      'city', 'state', 'rating', 'reviews', 'profile_url']

        import csv
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for company in companies:
                # Ensure all fields exist
                row = {field: company.get(field, '') for field in fieldnames}
                writer.writerow(row)

        self.logger.info(f"💾 Saved {len(companies)} companies to {csv_path}")

    def _append_to_csv(self, state_name, company_data):
        """Append a single company to CSV immediately (real-time save)"""
        import csv

        csv_path = self._get_state_csv_path(state_name)
        fieldnames = ['name', 'business_name', 'phone', 'website', 'address',
                      'city', 'state', 'rating', 'reviews', 'profile_url']

        # Check if file exists to decide on header
        file_exists = csv_path.exists() and csv_path.stat().st_size > 0

        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            row = {field: company_data.get(field, '') for field in fieldnames}
            writer.writerow(row)

    def _print_state_list(self):
        """Print all states with their status"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📋 ALL STATES LIST")
        self.logger.info("=" * 60)

        for i, state in enumerate(self.all_states, 1):
            name = state['name']
            if name in self.completed_states:
                status = "✅ COMPLETED"
                count = self.state_stats.get(name, {}).get('companies', 0)
                status += f" ({count} companies)"
            elif name == self.current_state:
                status = "🔄 IN PROGRESS"
            elif not self._should_include_state(name):
                status = "⏭️  SKIPPED (not in filter)"
            else:
                status = "⏳ PENDING"

            self.logger.info(f"  {i:02d}. {name:<20} {status}")

        self.logger.info("=" * 60)
        completed_count = len(self.completed_states)
        filtered_count = len([s for s in self.all_states if not self._should_include_state(s['name'])])
        pending_count = len(self.all_states) - completed_count - filtered_count

        self.logger.info(f"  ✅ Completed: {completed_count}")
        if self.state_names:
            self.logger.info(f"  ⏭️  Filtered:  {filtered_count}")
        self.logger.info(f"  ⏳ To Process: {pending_count}")
        self.logger.info("=" * 60 + "\n")

    def _should_include_state(self, state_name):
        """Check if state should be included based on whitelist"""
        if not self.state_names:
            return True  # No filter, include all
        return state_name.lower() in self.state_names

    def _extract_state_name(self, url):
        """Extract state name from URL"""
        # Pattern: /professionals/interior-designer/california-us-probr0-bo~t_11785~r_5332921
        match = re.search(r'/professionals/interior-designer/([a-z-]+)-us-probr0', url)
        if match:
            state_slug = match.group(1)
            # Convert slug to proper name
            state_name = state_slug.replace('-', ' ').title()
            return state_name
        return None

    def _extract_city_name(self, url):
        """Extract city name from URL"""
        # Pattern: /professionals/interior-designer/los-angeles-ca-us-probr0-bo~t_11785~r_5368361
        match = re.search(r'/professionals/interior-designer/([a-z-]+)-[a-z]{2}-us-probr0', url)
        if match:
            city_slug = match.group(1)
            city_name = city_slug.replace('-', ' ').title()
            return city_name
        return None

    def parse(self, response):
        """Parse the main page to get all state links"""
        self.logger.info(f"\n{'=' * 60}")
        self.logger.info("🏠 HOUZZ STATE-WISE SCRAPER")
        self.logger.info(f"{'=' * 60}")
        self.logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"Output directory: {self.output_dir}/")
        self.logger.info(f"{'=' * 60}\n")

        if response.status == 403:
            self.logger.error("Got 403 Forbidden - IP may be blocked")
            return

        # Find all state links
        state_links = response.css('a[href*="interior-designer"][href*="-us-probr0"]::attr(href)').getall()

        if not state_links:
            state_links = response.css('a.hz-browse-link::attr(href)').getall()
            state_links = [link for link in state_links if '-us-probr0' in link]

        # Build state list
        seen_states = set()
        for link in state_links:
            state_name = self._extract_state_name(link)
            if state_name and state_name not in seen_states:
                seen_states.add(state_name)
                self.all_states.append({
                    'name': state_name,
                    'url': urljoin(self.base_url, link)
                })

        self.logger.info(f"Found {len(self.all_states)} states")
        if self.state_names:
            self.logger.info(f"Filtering to: {', '.join(s.title() for s in self.state_names)}")

        # Print state list
        self._print_state_list()

        # Filter out completed states AND apply state name whitelist
        pending_states = [
            s for s in self.all_states
            if s['name'] not in self.completed_states
            and self._should_include_state(s['name'])
        ]

        if self.max_states:
            pending_states = pending_states[:self.max_states]

        self.logger.info(f"States to process: {len(pending_states)}")

        # Process states one at a time
        if pending_states:
            yield from self._start_next_state(pending_states)

    def _start_next_state(self, pending_states):
        """Start processing the next state"""
        if not pending_states:
            self._finish_scraping()
            return

        state = pending_states[0]
        self.current_state = state['name']
        self.current_state_companies = []
        self.state_queue = pending_states[1:]

        self.logger.info(f"\n{'#' * 60}")
        self.logger.info(f"# STATE: {state['name'].upper()}")
        self.logger.info(f"# Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"# Remaining: {len(pending_states)} states")
        self.logger.info(f"{'#' * 60}\n")

        yield scrapy.Request(
            state['url'],
            callback=self.parse_state,
            meta={'state': state, 'pending_states': pending_states[1:]},
            dont_filter=True
        )

    def parse_state(self, response):
        """Parse state page to get city links"""
        state = response.meta['state']
        pending_states = response.meta['pending_states']
        state_name = state['name']

        self.logger.info(f"📍 Parsing state: {state_name}")

        if response.status == 403:
            self.logger.error(f"Got 403 Forbidden for {state_name}")
            yield from self._complete_state(state_name, pending_states)
            return

        # Find city links
        city_links = response.css('a[href*="interior-designer"][href*="-us-probr0"]::attr(href)').getall()

        if not city_links:
            city_links = response.css('a.hz-browse-link::attr(href)').getall()

        # Filter to city-level links
        city_links = [link for link in city_links
                      if '-us-probr0' in link and link != response.url
                      and re.search(r'-[a-z]{2}-us-probr0', link)]

        # Remove duplicates
        city_links = list(dict.fromkeys(city_links))

        self.logger.info(f"   Found {len(city_links)} cities in {state_name}:")

        # Log city names
        cities_info = []
        for link in city_links:
            city_name = self._extract_city_name(link)
            if city_name:
                cities_info.append({'name': city_name, 'url': link})

        for i, city in enumerate(cities_info[:20], 1):  # Log first 20
            self.logger.info(f"      {i:02d}. {city['name']}")
        if len(cities_info) > 20:
            self.logger.info(f"      ... and {len(cities_info) - 20} more")

        if self.max_cities:
            city_links = city_links[:self.max_cities]

        # Process cities
        for i, link in enumerate(city_links):
            city_name = self._extract_city_name(link)
            full_url = urljoin(self.base_url, link)
            yield scrapy.Request(
                full_url,
                callback=self.parse_city_listings,
                meta={
                    'state': state,
                    'city_name': city_name or f"City_{i+1}",
                    'city_index': i + 1,
                    'total_cities': len(city_links),
                    'pending_states': pending_states
                }
            )

        # Also extract companies from state page
        yield from self.extract_companies(response, state_name, state_name)

        # If no cities found, complete state
        if not city_links:
            yield from self._complete_state(state_name, pending_states)

    def parse_city_listings(self, response):
        """Parse city listing page for companies"""
        state = response.meta['state']
        city_name = response.meta['city_name']
        city_index = response.meta['city_index']
        total_cities = response.meta['total_cities']
        pending_states = response.meta['pending_states']

        self.logger.info(f"   🏙️  [{city_index}/{total_cities}] {city_name}")

        if response.status == 403:
            self.logger.warning(f"      Got 403 for {city_name}")
            return

        # Extract companies
        yield from self.extract_companies(response, city_name, state['name'])

        # Handle pagination
        next_page = response.css('a.hz-pagination-link--next::attr(href)').get()
        if not next_page:
            next_page = response.css('a[rel="next"]::attr(href)').get()

        if next_page:
            next_url = urljoin(self.base_url, next_page)
            yield scrapy.Request(
                next_url,
                callback=self.parse_city_listings,
                meta=response.meta
            )

    def extract_companies(self, response, city_name, state_name):
        """Extract company links and follow to detail pages"""
        company_links = response.css('a.hz-pro-ctl::attr(href)').getall()

        if not company_links:
            company_links = response.css('a[href*="/pro/"]::attr(href)').getall()

        if not company_links:
            company_links = response.css('.hz-pro-search-results a::attr(href)').getall()
            company_links = [link for link in company_links if '/pro/' in link]

        new_count = 0
        for link in company_links:
            if link in self.seen_profiles:
                continue
            self.seen_profiles.add(link)
            new_count += 1

            full_url = urljoin(self.base_url, link)
            yield scrapy.Request(
                full_url,
                callback=self.parse_company_detail,
                meta={
                    'city_name': city_name,
                    'state_name': state_name
                }
            )

        if new_count > 0:
            self.logger.info(f"      Found {new_count} new companies")

    def parse_company_detail(self, response):
        """Parse company detail page"""
        city_name = response.meta.get('city_name', '')
        state_name = response.meta.get('state_name', '')

        if response.status == 403:
            return

        soup = BeautifulSoup(response.body, 'html.parser')

        data = {
            'profile_url': response.url,
            'name': '',
            'business_name': '',
            'phone': '',
            'website': '',
            'address': '',
            'city': city_name,
            'state': state_name,
            'rating': '',
            'reviews': '',
        }

        # Get company name
        name_elem = soup.find('h1')
        if name_elem:
            data['name'] = name_elem.get_text(strip=True)

        # Parse business section
        business_section = soup.find('section', id='business')
        if business_section:
            for div in business_section.find_all('div'):
                h3 = div.find('h3')
                if h3:
                    key = h3.get_text(strip=True)
                    p = div.find('p')
                    if p:
                        value = p.get_text(strip=True)
                        if 'Business Name' in key:
                            data['business_name'] = value
                        elif 'Phone' in key:
                            data['phone'] = value
                        elif 'Website' in key:
                            data['website'] = value
                        elif 'Address' in key or 'Location' in key:
                            data['address'] = value

        # Alternative phone
        if not data['phone']:
            phone_elem = soup.find('a', href=re.compile(r'^tel:'))
            if phone_elem:
                data['phone'] = phone_elem.get_text(strip=True)

        # Alternative website
        if not data['website']:
            website_elem = soup.find('a', {'data-component': 'Website'})
            if website_elem:
                data['website'] = website_elem.get('href', '')

        # Rating
        rating_elem = soup.find('span', class_=re.compile(r'rating'))
        if rating_elem:
            data['rating'] = rating_elem.get_text(strip=True)

        # Reviews
        review_elem = soup.find('span', class_=re.compile(r'review'))
        if review_elem:
            data['reviews'] = review_elem.get_text(strip=True)

        # Add to current state's companies and save immediately to CSV
        if data['name']:
            self.current_state_companies.append(data)
            # Save to CSV immediately (side by side / real-time)
            self._append_to_csv(state_name, data)

            # Log progress every 10 companies
            count = len(self.current_state_companies)
            if count % 10 == 0:
                self.logger.info(f"      💾 {state_name}: {count} companies saved to CSV")

        yield data

    def _complete_state(self, state_name, pending_states):
        """Complete current state and move to next"""
        # Save state data
        company_count = len(self.current_state_companies)
        self._save_state_to_csv(state_name, self.current_state_companies)

        # Update progress
        self.completed_states.add(state_name)
        self.state_stats[state_name] = {
            'companies': company_count,
            'completed_at': datetime.now().isoformat()
        }
        self._save_progress()

        self.logger.info(f"\n{'=' * 60}")
        self.logger.info(f"✅ STATE COMPLETE: {state_name}")
        self.logger.info(f"   Companies scraped: {company_count}")
        self.logger.info(f"   States completed: {len(self.completed_states)}/{len(self.all_states)}")
        self.logger.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"{'=' * 60}\n")

        # Start next state
        yield from self._start_next_state(pending_states)

    def _finish_scraping(self):
        """Called when all states are done"""
        elapsed = time.time() - self.start_time
        total_companies = sum(s.get('companies', 0) for s in self.state_stats.values())

        self.logger.info(f"\n{'=' * 60}")
        self.logger.info("🎉 SCRAPING COMPLETE!")
        self.logger.info(f"   Total states: {len(self.completed_states)}")
        self.logger.info(f"   Total companies: {total_companies}")
        self.logger.info(f"   Total time: {elapsed:.2f} seconds")
        self.logger.info(f"   Output: {self.output_dir}/")
        self.logger.info(f"{'=' * 60}\n")

        self._print_state_list()

    def closed(self, reason):
        """Called when spider closes"""
        # Save current state if interrupted
        if self.current_state and self.current_state_companies:
            self.logger.info(f"Saving partial data for {self.current_state}...")
            self._save_state_to_csv(self.current_state, self.current_state_companies)

        elapsed = time.time() - self.start_time
        total_companies = sum(s.get('companies', 0) for s in self.state_stats.values())

        self.logger.info(f"\nSpider closed: {reason}")
        self.logger.info(f"States completed: {len(self.completed_states)}")
        self.logger.info(f"Total companies: {total_companies}")
        self.logger.info(f"Total time: {elapsed:.2f} seconds")
