import yt_dlp
from pathlib import Path
import logging
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from .base import BaseScraper

logger = logging.getLogger(__name__)

class TwitchScraper(BaseScraper):
    """Twitch-specific implementation for video/audio downloading"""
    
    def __init__(self, segment_duration: int = 5, max_concurrent: int = 4):
        """Initialize Twitch scraper"""
        super().__init__(segment_duration, max_concurrent)
        
        # Twitch-specific audio settings
        self.audio_opts = {
            'format': 'Audio_Only/audio_only/worst',  # Twitch-specific format
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'postprocessor_args': [
                '-ar', '48000',  # Sample rate
                '-ac', '1',      # Mono channel
                '-acodec', 'pcm_s16le'  # 16-bit PCM encoding
            ],
            'download_ranges': None,  # Will be set per segment
            'extractor_args': {
                'twitch': {
                    'wait_for_video': '0',  # Don't wait for live streams
                }
            }
        }
    
    @staticmethod
    def can_handle_url(url: str) -> bool:
        """Check if the URL is a Twitch URL"""
        return any(domain in url.lower() for domain in [
            'twitch.tv',
            'www.twitch.tv',
            'clips.twitch.tv',
            'm.twitch.tv'
        ])
    
    def _get_video_info(self, url: str) -> dict:
        """Get video metadata from Twitch"""
        ydl_opts = {
            'quiet': True,
            'format': 'Audio_Only/audio_only/worst',
            'extractor_args': {
                'twitch': {
                    'wait_for_video': '0',
                }
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                return ydl.extract_info(url, download=False)
            except Exception as e:
                logger.error(f"Error extracting Twitch video info: {str(e)}")
                raise
    
    def _sanitize_title(self, title: str) -> str:
        """Sanitize the video title for filesystem compatibility"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            title = title.replace(char, '_')
        return title
    
    def _download_segment(self, url: str, output_dir: Path, segment: Dict) -> Path:
        """Download a single audio segment from Twitch"""
        segment_opts = {
            **self.audio_opts,
            'outtmpl': str(output_dir / f'segment_{segment["title"]}.%(ext)s'),
            'quiet': True,
            'progress': False,
            'retries': 3,
            'fragment_retries': 3,
        }
        
        # Add segment-specific download range
        if segment['end_time'] is not None:
            segment_opts['download_ranges'] = lambda info_dict, _: [{
                'start_time': segment['start_time'],
                'end_time': segment['end_time']
            }]
        
        try:
            with yt_dlp.YoutubeDL(segment_opts) as ydl:
                ydl.download([url])
            return output_dir / f'segment_{segment["title"]}.wav'
        except Exception as e:
            logger.error(f"Error downloading segment {segment['title']}: {str(e)}")
            raise
    
    def _get_segments(self, duration: float) -> List[Dict]:
        """Generate segment information for parallel downloading"""
        segments = []
        for i in range(int(duration / self.segment_duration) + 1):
            start_time = i * self.segment_duration
            end_time = min((i + 1) * self.segment_duration, duration)
            
            if end_time <= start_time:
                continue
                
            segments.append({
                'start_time': start_time,
                'end_time': end_time,
                'title': f'{i+1:03d}'
            })
        
        return segments
    
    def download(self, url: str, output_dir: Path) -> List[Path]:
        """Download audio from Twitch URL in parallel segments"""
        try:
            # Get video info and create segments
            info = self._get_video_info(url)
            duration = info.get('duration')
            
            if not duration:
                logger.warning("Could not determine video duration, downloading as single file")
                segments = [{'start_time': 0, 'end_time': None, 'title': 'full'}]
            else:
                segments = self._get_segments(duration)
            
            logger.info(f"Starting parallel download of {len(segments)} segments")
            segment_files = []
            
            # Download segments in parallel
            with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
                future_to_segment = {
                    executor.submit(self._download_segment, url, output_dir, segment): segment
                    for segment in segments
                }
                
                for future in as_completed(future_to_segment):
                    segment = future_to_segment[future]
                    try:
                        segment_path = future.result()
                        segment_files.append(segment_path)
                        logger.info(f"Completed segment {segment['title']}")
                    except Exception as e:
                        logger.error(f"Segment {segment['title']} failed: {str(e)}")
                        raise
            
            logger.info(f"All segments downloaded successfully")
            return sorted(segment_files)
            
        except Exception as e:
            logger.error(f"Error during parallel download: {str(e)}")
            raise
