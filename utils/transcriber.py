import logging
from pathlib import Path
from typing import List, BinaryIO
import subprocess
import io
import tempfile
from .formatters import get_formatter, JsonFormatter
from providers.gemini import GeminiProvider

logger = logging.getLogger(__name__)

class AudioTranscriber:
    """Handles audio transcription and diarization"""
    
    def __init__(self, provider: GeminiProvider, output_format: str = 'txt'):
        """
        Initialize transcriber
        
        Args:
            provider: LLM provider for transcription
            output_format (str): Output format (txt or json)
        """
        self.provider = provider
        self.formatter = get_formatter(output_format)
    
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
            
            # Clean up
            concat_list.unlink()
            for path in segment_paths:
                path.unlink()
            
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
            output_dir: Directory to save transcription
            video_id: Unique identifier for the video
            
        Returns:
            Path to the transcription file
        """
        try:
            # Combine segments into memory
            audio_data = self._combine_audio_segments(segment_paths)
            logger.info("Audio segments combined successfully")
            
            # Get transcription from provider
            logger.info(f"Starting transcription using {self.provider.name} {self.provider.version}")
            transcription = self.provider.transcribe_bytes(audio_data, self.formatter.get_prompt())
            
            if not transcription:
                raise ValueError("Transcription failed")
            
            # Format and save transcription
            formatted_text = self.formatter.format_output(transcription)
            extension = 'json' if isinstance(self.formatter, JsonFormatter) else 'txt'
            output_path = output_dir / f"{video_id}.{extension}"
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(formatted_text)
            
            logger.info(f"Transcription completed and saved to {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise 