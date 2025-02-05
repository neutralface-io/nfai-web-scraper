from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

class BaseScraper(ABC):
    """Abstract base class for platform-specific scrapers"""
    
    def __init__(self, segment_duration: int = 5, max_concurrent: int = 4):
        """
        Initialize base scraper
        
        Args:
            segment_duration (int): Duration of each segment in minutes
            max_concurrent (int): Maximum number of concurrent downloads
        """
        self.segment_duration = segment_duration * 60  # Convert to seconds
        self.max_concurrent = max_concurrent
    
    @staticmethod
    @abstractmethod
    def can_handle_url(url: str) -> bool:
        """Check if the scraper can handle this URL"""
        pass
    
    @abstractmethod
    def download(self, url: str, output_dir: Path) -> List[Path]:
        """Download content from URL"""
        pass 