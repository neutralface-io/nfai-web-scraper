from pathlib import Path
import logging
from typing import List
from scrapers.youtube import YouTubeScraper
from scrapers.twitch import TwitchScraper

logger = logging.getLogger(__name__)

class VideoDownloader:
    """Factory class for selecting appropriate platform-specific scraper"""
    
    def __init__(self, segment_duration: int = 5, max_concurrent: int = 4):
        """
        Initialize the video downloader
        
        Args:
            segment_duration (int): Duration of each segment in minutes
            max_concurrent (int): Maximum number of concurrent downloads
        """
        self.segment_duration = segment_duration
        self.max_concurrent = max_concurrent
        
        # Register platform scrapers
        self.scrapers = [
            YouTubeScraper(segment_duration, max_concurrent),
            TwitchScraper(segment_duration, max_concurrent),
            # Add other platform scrapers here
        ]
    
    def _get_scraper(self, url: str):
        """
        Get appropriate scraper for the URL
        
        Args:
            url (str): URL to process
            
        Returns:
            BaseScraper: Platform-specific scraper instance
        """
        for scraper in self.scrapers:
            if scraper.can_handle_url(url):
                return scraper
        raise ValueError(f"No scraper available for URL: {url}")
    
    def download(self, url: str, output_dir: Path) -> List[Path]:
        """
        Download audio from URL using appropriate platform scraper
        
        Args:
            url (str): URL to download from
            output_dir (Path): Directory to save the audio segments (video-specific)
            
        Returns:
            List[Path]: Paths to the downloaded audio segment files
        """
        try:
            # Create segments directory within video directory
            segments_dir = output_dir / 'segments'
            segments_dir.mkdir(parents=True, exist_ok=True)
            
            # Download using appropriate scraper
            scraper = self._get_scraper(url)
            segment_paths = scraper.download(url, segments_dir)
            
            logger.info(f"Downloaded {len(segment_paths)} segments to {segments_dir}")
            return segment_paths
            
        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            raise 