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

## Usage

### Basic Usage

Process a video with default settings (TXT format):
```bash
python process_video.py --url "https://youtube.com/watch?v=example"
```

### Advanced Usage

Configure segment duration and parallel processing:
```bash
python process_video.py \
    --url "https://www.twitch.tv/videos/12345678" \
    --output_dir "custom_output" \
    --segment_duration 10 \
    --max_concurrent 6 \
    --format json \
    --api_key "your-gemini-api-key"
```

### Arguments

- `--url`: Video URL (required)
- `--output_dir`: Output directory (default: "output")
- `--format`: Output format (json/txt, default: txt)
- `--segment_duration`: Duration of each segment in minutes (default: 5)
- `--max_concurrent`: Maximum number of concurrent downloads (default: 4)
- `--api_key`: Gemini API key (optional if set via environment variable)

## Output Formats

### Text Format (Default)
Semicolon-delimited format with precise timestamps:
```
00:00:00.000;Speaker 1;Hello, welcome to the video.
00:00:03.450;Speaker 2;Thanks for having me here.
00:00:07.200;Speaker 1;Let's discuss the topic.
```

### JSON Format
Structured format with precise timestamps:
```json
{
  "segments": [
    {
      "timestamp": "00:00:00.000",
      "speaker": "Speaker 1",
      "transcription": "Hello, welcome to the video."
    },
    {
      "timestamp": "00:00:03.450",
      "speaker": "Speaker 2",
      "transcription": "Thanks for having me here."
    }
  ]
}
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