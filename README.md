# Video Processing Pipeline

A Python-based CLI tool that processes videos from various social media platforms, optimized for AI training data generation. The tool downloads videos, extracts audio in segments, and prepares them for transcription and diarization.

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

## Usage

### Basic Usage

Download a video with default settings:
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
    --max_concurrent 6
```

### Arguments

- `--url`: Video URL (required)
- `--output_dir`: Output directory (default: "output")
- `--format`: Output format (json/txt, default: json)
- `--segment_duration`: Duration of each segment in minutes (default: 5)
- `--max_concurrent`: Maximum number of concurrent downloads (default: 4)

## Output Format

The tool generates:
1. Audio segments in WAV format:
   - 48kHz sample rate
   - Mono channel
   - 16-bit PCM encoding
2. Organized by sequential segment numbers
3. Ready for transcription/diarization processing

## Supported URLs

### YouTube
- Regular videos: `youtube.com/watch?v=...`
- Short URLs: `youtu.be/...`
- Mobile URLs: `m.youtube.com/...`

### Twitch
- VODs: `twitch.tv/videos/...`
- Clips: `clips.twitch.tv/...`
- Channel URLs: `twitch.tv/channel_name/video/...`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License
