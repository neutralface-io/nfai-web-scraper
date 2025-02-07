# Video Processing Pipeline

A Python-based CLI tool that processes videos from various social media platforms, optimized for AI training data generation. The tool downloads videos, extracts audio in segments, and performs AI-powered transcription and speaker diarization.

## Features

- **Multi-Platform Support**:
  - YouTube videos and playlists
  - Twitch VODs and clips
  - More platforms coming soon

- **Optimized Audio Processing**:
  - Parallel segment downloading
  - Speech-optimized audio format (48kHz, mono, 16-bit PCM)
  - Configurable segment duration
  - Memory-efficient processing
  - Automatic cleanup of temporary files

- **AI-Powered Transcription**:
  - Speaker diarization using Gemini AI
  - Automatic speaker identification
  - High-precision timestamps (HH:MM:SS.mmm)
  - Multiple output formats
  - Context-aware processing

- **Smart Resource Management**:
  - Automatic platform detection
  - Configurable concurrent downloads
  - Progress tracking
  - Robust error handling and retries
  - Memory-optimized audio handling

- **X (formerly Twitter) Data Collection**:
  - Environment-based configuration
  - Secure credential management
  - Cookie-based session handling
  - Automatic authentication
  - Complete tweet history download
  - Rich tweet metadata
  - Media URL extraction
  - Progress tracking
  - More features coming soon...

## Prerequisites

- Python 3.8 or higher
- FFmpeg installed on your system:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install ffmpeg

  # macOS
  brew install ffmpeg

  # Windows (using Chocolatey)
  choco install ffmpeg
  ```
- Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

For X functionality:
- X account credentials
- Python 3.8 or higher
- Required Python packages (see requirements.txt)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd video-processing-pipeline
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Gemini API key:
```bash
# Option 1: Environment variable
export GEMINI_API_KEY="your-api-key"

# Option 2: Provide via command line argument
```

## Configuration

### X Credentials

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit .env with your X credentials:
```bash
# X (formerly Twitter) Credentials
X_USERNAME=your_username
X_EMAIL=your_email@example.com
X_PASSWORD=your_password
```

## Usage

### Basic Usage

Process a video with default settings (TXT format):
```bash
# Process video with default JSON output
python process_video.py --url "https://youtube.com/watch?v=example"

# Specify TXT output format
python process_video.py --url "https://youtube.com/watch?v=example" --format txt
```

### Advanced Usage

Configure segment duration and parallel processing:
```bash
python process_video.py \
    --url "https://www.twitch.tv/videos/12345678" \
    --output_dir "custom_output" \
    --segment_duration 10 \
    --max_concurrent 6 \
    --api_key "your-gemini-api-key"
```

### Arguments

- `--url`: Video URL (required)
- `--output_dir`: Output directory (default: "output")
- `--format`: Output format (json/txt, default: json)
- `--segment_duration`: Duration of each segment in minutes (default: 5)
- `--max_concurrent`: Maximum number of concurrent downloads (default: 4)
- `--api_key`: Gemini API key (optional if set via environment variable)

### X Data Collection

Basic usage:
```bash
python scrape_x.py --output_dir "x_data"
```

Download tweets from a user:
```bash
python scrape_x.py \
    --output_dir "x_data" \
    --username "example_user"
```

Download with limits:
```bash
python scrape_x.py \
    --output_dir "x_data" \
    --username "example_user" \
    --max_tweets 1000 \
    --since_date "2024-01-01"
```

With custom cookies path:
```bash
python scrape_x.py \
    --output_dir "x_data" \
    --cookies_path "custom_cookies.json" \
    --username "example_user"
```

### Arguments for X Scraper

- `--output_dir`: Output directory for downloaded data (default: "output")
- `--cookies_path`: Path to save/load cookies (optional)
- `--username`: X username to download tweets from (without @ symbol)
- `--max_tweets`: Maximum number of tweets to download (default: all)
- `--since_date`: Only get tweets after this date (format: YYYY-MM-DD)
- `--requests_per_second`: Maximum number of requests per second (default: 10)

### Rate Limiting

The scraper includes built-in rate limiting to prevent API throttling:

- Default rate: 10 requests per second
- Configurable burst limit (default: 3 requests)
- Automatic retry on rate limit errors
- Respects Twitter's rate limit headers
- Exponential backoff for retries

You can configure the rate limiter when initializing the scraper:

```python
scraper = XScraper(
    requests_per_second=0.5,  # Adjust request rate
    burst_limit=3,           # Maximum burst size
    cookies_path="cookies.json"
)
```

### X Output Format

Tweets are saved in JSON format with rich metadata:
```json
{
  "user": {
    "id": "123456789",
    "username": "example_user",
    "name": "Example Name",
    "description": "User bio",
    "followers": 1000,
    "following": 500,
    "tweets": 5000,
    "joined": "2020-01-01T00:00:00Z"
  },
  "tweets": [
    {
      "id": "987654321",
      "created_at": "2023-01-01T12:00:00Z",
      "text": "Example tweet text",
      "likes": 42,
      "retweets": 7,
      "replies": 3,
      "is_retweet": false,
      "is_reply": false,
      "language": "en",
      "urls": ["https://example.com"],
      "media": [
        {
          "type": "photo",
          "url": "https://example.com/image.jpg",
          "preview_url": "https://example.com/preview.jpg"
        }
      ]
    }
  ],
  "metadata": {
    "downloaded_at": "2024-02-05T12:00:00Z",
    "tweet_count": 1000
  }
}
```

## Output Formats

### Text Format
Semicolon-delimited format with precise timestamps:
```
00:00:00.000;Speaker 1;Hello, welcome to the video.
00:00:03.450;Speaker 2;Thanks for having me here.
00:00:07.200;Speaker 1;Let's discuss the topic.
```

### JSON Format (Default)
Structured format with precise timestamps:
```json
{
  "segments": [
    {
      "timestamp": "00:00:00.000",
      "speaker": "Speaker 1",
      "text": "Hello, welcome to the video."
    },
    {
      "timestamp": "00:00:03.450",
      "speaker": "Speaker 2",
      "text": "Thanks for having me here."
    }
  ],
  "speaker_clips": {
    "Speaker 1": "speaker_clips/speaker_1.wav",
    "Speaker 2": "speaker_clips/speaker_2.wav"
  }
}
```

## Output Structure
```
output/
├── video_id/
│   ├── speaker_clips/      # Speaker-specific audio clips
│   │   ├── speaker_1.wav
│   │   └── speaker_2.wav
│   ├── video_id_processed.wav  # Combined audio file
│   └── video_id.json          # Transcription output (or .txt)
```

## Supported URLs

### YouTube
- Regular videos: `https://youtube.com/watch?v=VIDEO_ID`
- Short URLs: `https://youtu.be/VIDEO_ID`
- Playlist items: `https://youtube.com/playlist?list=PLAYLIST_ID`

### Twitch
- VODs: `https://www.twitch.tv/videos/VOD_ID`
- Clips: `https://clips.twitch.tv/CLIP_ID`

## Output Files

Files are saved using the video's unique identifier:
- Text format: `{video_id}.txt`
- JSON format: `{video_id}.json`

## Error Handling

The tool includes robust error handling:
- Automatic retries for failed downloads
- Exponential backoff for API requests
- Detailed error logging
- Cleanup of temporary files
- Memory-efficient processing