import os
import logging
import json
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
from twikit import Client, TooManyRequests
from dotenv import load_dotenv
import time
import asyncio

logger = logging.getLogger(__name__)

class RateLimiter:
    """Token bucket rate limiter"""
    def __init__(self, rate: float, burst: int = 1):
        """
        Initialize rate limiter
        
        Args:
            rate: Number of requests per second
            burst: Maximum burst size
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire a token, waiting if necessary"""
        async with self.lock:
            while self.tokens <= 0:
                now = time.monotonic()
                time_passed = now - self.last_update
                self.tokens = min(
                    self.burst,
                    self.tokens + time_passed * self.rate
                )
                self.last_update = now
                if self.tokens <= 0:
                    await asyncio.sleep(1 / self.rate)
            
            self.tokens -= 1
            self.last_update = time.monotonic()

class XScraper:
    """Handles X (formerly Twitter) data scraping operations"""
    
    def __init__(
        self, 
        cookies_path: Optional[Path] = None,
        requests_per_second: float = 0.5,  # Default to 1 request every 2 seconds
        burst_limit: int = 3  # Allow bursts of up to 3 requests
    ):
        """
        Initialize X scraper
        
        Args:
            cookies_path: Path to save/load cookies (default: current directory)
            requests_per_second: Maximum requests per second
            burst_limit: Maximum number of requests in a burst
        """
        # Load environment variables
        load_dotenv()
        
        # Get credentials
        self.username = os.getenv('X_USERNAME')
        self.email = os.getenv('X_EMAIL')
        self.password = os.getenv('X_PASSWORD')
        
        if not all([self.username, self.email, self.password]):
            raise ValueError(
                "X credentials not found. Please set X_USERNAME, "
                "X_EMAIL, and X_PASSWORD environment variables"
            )
        
        # Initialize client
        self.client = Client('en-US')
        self.cookies_path = cookies_path or Path('x_cookies.json')
        self._authenticated = False
        
        self.rate_limiter = RateLimiter(requests_per_second, burst_limit)
    
    async def authenticate(self) -> None:
        """Authenticate with X"""
        try:
            await self.client.login(
                auth_info_1=self.username,
                auth_info_2=self.email,
                password=self.password,
                cookies_file=str(self.cookies_path)
            )
            self._authenticated = True
            logger.info("Successfully authenticated with X")
            
        except Exception as e:
            logger.error(f"Failed to authenticate with X: {str(e)}")
            raise 

    async def get_user_tweets(
        self, 
        username: str, 
        output_dir: Path, 
        max_tweets: Optional[int] = None,
        since_date: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 60.0
    ) -> Path:
        """Download tweets from a user"""
        if not self._authenticated:
            await self.authenticate()
        
        try:
            # Parse since_date if provided
            since_timestamp = None
            if since_date:
                try:
                    since_timestamp = datetime.strptime(since_date, "%Y-%m-%d")
                    logger.info(f"Downloading tweets since {since_date}")
                except ValueError:
                    raise ValueError("since_date must be in YYYY-MM-DD format")
            
            # Get user info first
            logger.info(f"Getting user info for @{username}")
            user = await self.client.get_user_by_screen_name(username)
            if not user:
                raise ValueError(f"User @{username} not found")
            
            logger.info(f"Downloading {'all' if max_tweets is None else max_tweets} tweets from @{username}")
            tweets = []
            seen_tweet_ids = set()  # Track seen tweet IDs
            reached_date_limit = False  # Flag for date threshold
            
            retry_count = 0
            while retry_count < max_retries:
                try:
                    # Get initial batch of tweets
                    await self.rate_limiter.acquire()
                    user_tweets = await self.client.get_user_tweets(
                        user.id,
                        "Tweets",
                        count=100
                    )
                    
                    while user_tweets:
                        tweets_added_in_batch = 0
                        reached_date_limit_in_batch = False
                        
                        # Process tweets in this batch
                        for tweet in user_tweets:
                            # Check if we've hit the tweet limit
                            if max_tweets and len(tweets) >= max_tweets:
                                logger.info(f"Reached maximum tweet count: {max_tweets}")
                                break
                            
                            try:
                                # Skip if we've seen this tweet before
                                if tweet.id in seen_tweet_ids:
                                    logger.debug(f"Skipping duplicate tweet {tweet.id}")
                                    continue
                                
                                # Parse tweet date
                                if tweet.created_at:
                                    tweet_date = datetime.strptime(
                                        tweet.created_at,
                                        "%a %b %d %H:%M:%S %z %Y"
                                    )
                                    
                                    # Check if we've reached tweets older than since_date
                                    if since_timestamp and tweet_date.date() < since_timestamp.date():
                                        logger.debug(
                                            f"Found tweet from {tweet_date.date()} "
                                            f"(before {since_timestamp.date()}), skipping batch"
                                        )
                                        reached_date_limit_in_batch = True
                                        break
                                    
                                    formatted_date = tweet_date.isoformat()
                                else:
                                    formatted_date = None
                                
                                # Start with basic attributes that should always exist
                                tweet_data = {
                                    'id': tweet.id,
                                    'created_at': formatted_date,
                                    'text': tweet.text
                                }
                                
                                # Optionally add engagement metrics if they exist
                                for attr in ['favorite_count', 'retweet_count', 'reply_count']:
                                    if hasattr(tweet, attr):
                                        tweet_data[attr] = getattr(tweet, attr)
                                
                                # Add URLs if they exist
                                if hasattr(tweet, 'urls') and tweet.urls:
                                    tweet_data['urls'] = [
                                        url.get('expanded_url') if isinstance(url, dict) 
                                        else url.expanded_url 
                                        for url in tweet.urls
                                        if (isinstance(url, dict) and url.get('expanded_url')) or 
                                        hasattr(url, 'expanded_url')
                                    ]
                                
                                # Add media if it exists
                                if hasattr(tweet, 'media') and tweet.media:
                                    tweet_data['media'] = []
                                    for media in tweet.media:
                                        media_data = {}
                                        for attr in ['type', 'url', 'preview_url']:
                                            if hasattr(media, attr):
                                                media_data[attr] = getattr(media, attr)
                                    if media_data:
                                        tweet_data['media'].append(media_data)
                                
                                tweets.append(tweet_data)
                                seen_tweet_ids.add(tweet.id)
                                tweets_added_in_batch += 1
                                
                            except Exception as e:
                                logger.warning(
                                    f"Error processing tweet {getattr(tweet, 'id', 'unknown')}: {str(e)}"
                                )
                                continue
                        
                        # Break conditions
                        if max_tweets and len(tweets) >= max_tweets:
                            reached_date_limit = True
                            break
                        
                        # Log batch progress
                        logger.info(
                            f"Fetched {len(tweets)} tweets so far "
                            f"(+{tweets_added_in_batch} in this batch)"
                        )
                        
                        if reached_date_limit_in_batch and tweets_added_in_batch == 0:
                            # If we found no new tweets in this batch and hit the date limit,
                            # we can stop fetching
                            logger.info(f"Reached date threshold {since_date}, stopping collection")
                            reached_date_limit = True
                            break
                        
                        # Get next batch of tweets
                        try:
                            await self.rate_limiter.acquire()
                            user_tweets = await user_tweets.next()
                        except TooManyRequests as e:
                            retry_count += 1
                            if retry_count >= max_retries:
                                raise
                            wait_time = float(e.headers.get('x-rate-limit-reset', retry_delay))
                            logger.info(f"Rate limit hit, waiting {wait_time} seconds before retry {retry_count}/{max_retries}")
                            await asyncio.sleep(wait_time)
                        except Exception as e:
                            logger.debug(f"No more tweets available: {str(e)}")
                            break
                        
                        await asyncio.sleep(0.5)
                    
                    if reached_date_limit:
                        break
                    
                    # If we get here, we've successfully completed
                    break
                    
                except TooManyRequests as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        raise
                    wait_time = float(e.headers.get('x-rate-limit-reset', retry_delay))
                    logger.info(f"Rate limit hit, waiting {wait_time} seconds before retry {retry_count}/{max_retries}")
                    await asyncio.sleep(wait_time)
            
            if not tweets:
                logger.warning(f"No tweets were successfully processed for @{username}")
            
            # Save tweets to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"{username}_tweets_{timestamp}.json"
            
            tweet_data = {
                'user': {
                    'id': user.id,
                    'username': user.screen_name,
                    'name': user.name,
                    'description': user.description,
                    'followers': user.followers_count,
                    'following': user.following_count,
                    'tweets': user.statuses_count,
                    'joined': user.created_at
                },
                'tweets': tweets,
                'metadata': {
                    'downloaded_at': datetime.now().isoformat(),
                    'tweet_count': len(tweets)
                }
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(tweet_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Successfully downloaded {len(tweets)} tweets to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to download tweets from @{username}: {str(e)}")
            raise 
        