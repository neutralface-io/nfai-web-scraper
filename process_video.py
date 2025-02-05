import argparse
from pathlib import Path
from utils.downloader import VideoDownloader
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process video content with transcription and diarization')
    parser.add_argument('--url', type=str, required=True, help='URL of the video to process')
    parser.add_argument('--output_dir', type=str, default='output', help='Output directory for processed files')
    parser.add_argument('--format', type=str, default='json', choices=['json', 'txt'], help='Output format')
    parser.add_argument('--segment_duration', type=int, default=5, help='Duration of each video segment in minutes')
    parser.add_argument('--max_concurrent', type=int, default=4, help='Maximum number of concurrent downloads')
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Initialize downloader with parallel processing settings
        downloader = VideoDownloader(
            segment_duration=args.segment_duration,
            max_concurrent=args.max_concurrent
        )
        
        # Download video segments
        logger.info(f"Downloading video from: {args.url}")
        segment_paths = downloader.download(args.url, output_dir)
        logger.info(f"Downloaded {len(segment_paths)} segments successfully")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main() 