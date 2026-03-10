#!/usr/bin/env python3
"""
Run the Houzz State-wise Spider

Usage:
    python run_spider.py                                    # Scrape all states
    python run_spider.py --states 5                         # Limit to 5 states
    python run_spider.py --states 2 --cities 3              # 2 states, 3 cities each
    python run_spider.py --state-names Washington "New York"  # Specific states only
    python run_spider.py --output my_data                   # Custom output directory
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Houzz State-wise Scraper')
    parser.add_argument('--states', type=int, default=None,
                        help='Maximum number of states to scrape (default: all)')
    parser.add_argument('--cities', type=int, default=None,
                        help='Maximum number of cities per state (default: all)')
    parser.add_argument('--state-names', nargs='+', type=str, default=None,
                        help='Specific states to scrape (e.g., Washington "New York"). If not specified, scrapes all states.')
    parser.add_argument('--output', type=str, default='state_data',
                        help='Output directory for state CSV files (default: state_data)')
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Log level (default: INFO)')
    args = parser.parse_args()

    # Change to the scrapy project directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)

    print("\n" + "=" * 60)
    print("🏠 HOUZZ STATE-WISE SCRAPER (Scrapy)")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Max states:           {args.states or 'All'}")
    print(f"  Max cities per state: {args.cities or 'All'}")
    if args.state_names:
        print(f"  State filter:         {', '.join(args.state_names)}")
    print(f"  Output directory:     {output_dir.absolute()}/")
    print(f"  Log level:            {args.log_level}")
    print()
    print("Output files will be:")
    print(f"  {output_dir}/houzz_alabama.csv")
    print(f"  {output_dir}/houzz_alaska.csv")
    print(f"  {output_dir}/houzz_arizona.csv")
    print(f"  ... (one CSV per state)")
    print(f"  {output_dir}/progress.json")
    print()

    # Build scrapy command
    cmd = [
        sys.executable, '-m', 'scrapy', 'crawl', 'houzz',
        '-a', f'output_dir={args.output}',
        '-s', f'LOG_LEVEL={args.log_level}',
    ]

    if args.states:
        cmd.extend(['-a', f'max_states={args.states}'])
    if args.cities:
        cmd.extend(['-a', f'max_cities={args.cities}'])
    if args.state_names:
        # Join state names with comma separator for passing to spider
        state_names_str = ','.join(args.state_names)
        cmd.extend(['-a', f'state_names={state_names_str}'])

    print(f"Command: {' '.join(cmd)}")
    print("=" * 60)
    print()

    # Run scrapy
    try:
        subprocess.run(cmd, check=True)
        print("\n" + "=" * 60)
        print("🎉 Scraping completed!")
        print(f"Output saved to: {output_dir.absolute()}/")
        print("=" * 60)
    except KeyboardInterrupt:
        print("\n\n⚠️ Scraping interrupted by user")
        print(f"Partial results saved to: {output_dir.absolute()}/")
        print("Run again to resume from where you left off.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running spider: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
