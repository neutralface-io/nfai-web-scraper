import logging
from pathlib import Path
from typing import List, BinaryIO
import subprocess
import io
import tempfile
from .formatters import get_formatter, JsonFormatter
from providers.gemini import GeminiProvider
from utils.speaker_clipper import SpeakerClipper
import json

logger = logging.getLogger(__name__)

class AudioTranscriber:
    """Handles audio transcription and diarization"""
    
    def __init__(self, provider: GeminiProvider, output_format: str = 'json', clip_duration: int = 30):
        """
        Initialize transcriber
        
        Args:
            provider: LLM provider for transcription
            output_format (str): Output format (json or txt, default: json)
            clip_duration: Duration of clips in seconds
        """
        self.provider = provider
        self.formatter = get_formatter(output_format)
        self.clip_duration = clip_duration
        self.speaker_clipper = SpeakerClipper(clip_duration=clip_duration)
    
    def _combine_audio_segments(self, segment_paths: List[Path]) -> bytes:
        """
        Combine multiple WAV segments into a single in-memory buffer
        
        Args:
            segment_paths: List of paths to audio segments
            
        Returns:
            bytes: Combined audio data
        """
        try:
            # Create a temporary file listing segments
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for path in sorted(segment_paths):
                    f.write(f"file '{path.absolute()}'\n")
                concat_list = Path(f.name)
            
            # Use FFmpeg to combine segments and output to pipe
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_list),
                '-c', 'copy',
                '-f', 'wav',
                'pipe:1'  # Output to stdout
            ]
            
            logger.info("Combining audio segments...")
            process = subprocess.run(
                cmd, 
                check=True, 
                capture_output=True
            )
            
            if not process.stdout:
                raise ValueError("FFmpeg produced no output")
            
            logger.info(f"Combined audio size: {len(process.stdout) / (1024*1024):.2f} MB")
            
            # Clean up concat list and segments
            concat_list.unlink()
            for path in segment_paths:
                path.unlink()
            
            # Clean up segments directory if empty
            segments_dir = path.parent
            if not any(segments_dir.iterdir()):
                segments_dir.rmdir()
                logger.info("Removed empty segments directory")
            
            return process.stdout
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise
        except Exception as e:
            logger.error(f"Error combining audio segments: {str(e)}")
            raise
    
    def transcribe(self, segment_paths: List[Path], output_dir: Path, video_id: str) -> Path:
        """
        Transcribe and diarize audio segments
        
        Args:
            segment_paths: List of paths to audio segments
            output_dir: Video-specific directory for outputs
            video_id: Unique identifier for the video
            
        Returns:
            Path to the transcription file
        """
        try:
            # Combine segments into memory
            audio_data = self._combine_audio_segments(segment_paths)
            logger.info("Audio segments combined successfully")
            
            # Create processed audio file in video directory
            processed_audio = output_dir / f"{video_id}_processed.wav"
            with open(processed_audio, 'wb') as f:
                f.write(audio_data)
            
            # Get transcription from provider
            logger.info(f"Starting transcription using {self.provider.name}")
            result = self.provider.transcribe(processed_audio, self.formatter.get_prompt())
            if not result:
                raise ValueError("Transcription failed")
            
            # Parse transcription result
            segments = self.formatter.parse_transcription(result)
            
            # Extract speaker clips
            logger.info("Extracting speaker clips...")
            speaker_clips = self.speaker_clipper.extract_speaker_clips(
                processed_audio,
                segments,
                output_dir
            )
            logger.info(f"Extracted {len(speaker_clips)} speaker clips")
            
            # Save output based on format
            if isinstance(self.formatter, JsonFormatter):
                # JSON format
                output_path = output_dir / f"{video_id}.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'segments': segments,
                        'speaker_clips': {
                            speaker: str(path.relative_to(output_dir))
                            for speaker, path in speaker_clips.items()
                        }
                    }, f, indent=2)
            else:
                # Text format
                output_path = output_dir / f"{video_id}.txt"
                with open(output_path, 'w', encoding='utf-8') as f:
                    for segment in segments:
                        f.write(f"{segment['timestamp']};{segment['speaker']};{segment['text']}\n")
            
            logger.info(f"Transcription saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise 