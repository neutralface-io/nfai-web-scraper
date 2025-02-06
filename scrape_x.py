import asyncio
import argparse
import logging
from pathlib import Path
from scrapers.x_scraper import XScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Download data from X (formerly Twitter)')
    parser.add_argument('--output_dir', type=str, default='output', 
                       help='Output directory for downloaded data')
    parser.add_argument('--cookies_path', type=str, 
                       help='Path to save/load cookies (optional)')
    parser.add_argument('--username', type=str,
                       help='X username to download tweets from (without @ symbol)')
    parser.add_argument('--max_tweets', type=int,
                       help='Maximum number of tweets to download (default: all)')
    parser.add_argument('--since_date', type=str,
                       help='Only get tweets after this date (format: YYYY-MM-DD)')
    parser.add_argument('--requests_per_second', type=float, default=10.0,
                       help='Maximum number of requests per second (default: 10)')
    return parser.parse_args()

async def main():
    args = parse_arguments()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize scraper
    cookies_path = Path(args.cookies_path) if args.cookies_path else None
    scraper = XScraper(
        cookies_path=cookies_path,
        requests_per_second=args.requests_per_second
    )
    
    try:
        # Download tweets if username provided
        if args.username:
            output_file = await scraper.get_user_tweets(
                args.username, 
                output_dir,
                max_tweets=args.max_tweets,
                since_date=args.since_date
            )
            logger.info(f"Tweets saved to: {output_file}")
        else:
            logger.error("No username provided. Use --username to specify an X user")
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 