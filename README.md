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
  - Efficient resource usage

- **AI-Powered Transcription**:
  - Speaker diarization using Gemini AI
  - Automatic speaker identification
  - Multiple output formats (TXT, JSON)
  - Timestamp precision
  - Context-aware processing

- **Smart Download Management**:
  - Automatic platform detection
  - Configurable concurrent downloads
  - Progress tracking per segment
  - Robust error handling

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

Download and transcribe a video with default settings (TXT format):
```bash
python process_video.py --url "https://youtube.com/watch?v=example"
```

### Advanced Usage

Configure segment duration, parallel processing, and output format:
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
- `--time_unit`: Time unit for timestamps (ms/s/min, default: ms)
- `--segment_duration`: Duration of each segment in minutes (default: 5)
- `--max_concurrent`: Maximum number of concurrent downloads (default: 4)
- `--api_key`: Gemini API key (optional if set via environment variable)

## Output Formats

### Text Format (Default)
Semicolon-delimited format with configurable timestamps:

**Milliseconds (default)**:
```
0;Speaker 1;Hello, welcome to the video.
3500;Speaker 2;Thanks for having me here.
7200;Speaker 1;Let's discuss the topic.
```

**Seconds**:
```
0.0;Speaker 1;Hello, welcome to the video.
3.5;Speaker 2;Thanks for having me here.
7.2;Speaker 1;Let's discuss the topic.
```

**Minutes**:
```
0.000;Speaker 1;Hello, welcome to the video.
0.058;Speaker 2;Thanks for having me here.
0.120;Speaker 1;Let's discuss the topic.
```

### JSON Format
Structured format with configurable timestamps:

**Milliseconds (default)**:
```json
{
  "segments": [
    {
      "timestamp_ms": 0,
      "speaker": "Speaker 1",
      "transcription": "Hello, welcome to the video."
    },
    {
      "timestamp_ms": 3500,
      "speaker": "Speaker 2",
      "transcription": "Thanks for having me here."
    }
  ]
}
```

**Seconds**:
```json
{
  "segments": [
    {
      "timestamp_s": 0.0,
      "speaker": "Speaker 1",
      "transcription": "Hello, welcome to the video."
    },
    {
      "timestamp_s": 3.5,
      "speaker": "Speaker 2",
      "transcription": "Thanks for having me here."
    }
  ]
}
```

**Minutes**:
```json
{
  "segments": [
    {
      "timestamp_min": 0.000,
      "speaker": "Speaker 1",
      "transcription": "Hello, welcome to the video."
    },
    {
      "timestamp_min": 0.058,
      "speaker": "Speaker 2",
      "transcription": "Thanks for having me here."
    }
  ]
}
```

### Example Usage with Time Units

Basic usage with milliseconds (default):
```bash
python process_video.py --url "https://youtube.com/watch?v=example"
```

Using seconds for timestamps:
```bash
python process_video.py --url "https://youtube.com/watch?v=example" --time_unit s
```

JSON format with minutes:
```bash
python process_video.py --url "https://youtube.com/watch?v=example" --format json --time_unit min
```

## Supported URLs

### YouTube
- Regular videos: `