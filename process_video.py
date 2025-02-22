import argparse
from pathlib import Path
from utils.downloader import VideoDownloader
from utils.transcriber import AudioTranscriber
import logging
import os
import warnings
from providers.gemini import GeminiProvider
from utils.url_parser import extract_video_id

# Suppress gRPC warnings
warnings.filterwarnings('ignore', category=UserWarning)

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
    parser.add_argument('--format', type=str, default='json', choices=['json', 'txt'], 
                       help='Output format (default: json)')
    parser.add_argument('--segment_duration', type=int, default=5, help='Duration of each segment in minutes')
    parser.add_argument('--max_concurrent', type=int, default=4, help='Maximum number of concurrent downloads')
    parser.add_argument('--api_key', type=str, help='Gemini API key (or set GEMINI_API_KEY env var)')
    parser.add_argument('--clip_duration', type=int, default=30,
                       help='Duration of speaker clips in seconds (default: 30)')
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Get video ID from URL
    video_id = extract_video_id(args.url)
    logger.info(f"Processing video ID: {video_id}")
    
    # Get API key from args or environment
    api_key = args.api_key or os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("Gemini API key must be provided via --api_key or GEMINI_API_KEY environment variable")
    
    # Create base output directory
    base_output_dir = Path(args.output_dir)
    base_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create video-specific directory
    video_dir = base_output_dir / video_id
    video_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Download audio segments
        downloader = VideoDownloader(
            segment_duration=args.segment_duration,
            max_concurrent=args.max_concurrent
        )
        
        logger.info(f"Downloading video from: {args.url}")
        segment_paths = downloader.download(args.url, video_dir)
        logger.info(f"Downloaded {len(segment_paths)} segments successfully")
        
        # Initialize provider and transcriber
        provider = GeminiProvider(api_key=api_key)
        transcriber = AudioTranscriber(
            provider=provider,
            output_format=args.format,
            clip_duration=args.clip_duration
        )
        
        # Transcribe and diarize
        logger.info(f"Starting transcription and diarization in {args.format} format")
        transcription_path = transcriber.transcribe(segment_paths, video_dir, video_id)
        logger.info(f"Transcription saved to: {transcription_path}")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main() 