import logging
import google.generativeai as genai
from pathlib import Path
from typing import List, Dict
import time
import subprocess
import tempfile
from .formatters import get_formatter, JsonFormatter

logger = logging.getLogger(__name__)

class GeminiTranscriber:
    """Handles audio transcription and diarization using Gemini API"""
    
    def __init__(self, api_key: str, max_retries: int = 3, output_format: str = 'txt'):
        """
        Initialize Gemini transcriber
        
        Args:
            api_key (str): Gemini API key
            max_retries (int): Maximum number of retry attempts
            output_format (str): Output format (txt or json)
        """
        self.max_retries = max_retries
        self.formatter = get_formatter(output_format)
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def _combine_audio_segments(self, segment_paths: List[Path], output_dir: Path) -> Path:
        """
        Combine multiple WAV segments into a single file using FFmpeg
        
        Args:
            segment_paths (List[Path]): List of paths to audio segments
            output_dir (Path): Directory to save combined file
            
        Returns:
            Path: Path to combined audio file
        """
        try:
            # Create a temporary file listing all segments
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for path in sorted(segment_paths):
                    f.write(f"file '{path.absolute()}'\n")
                concat_list = Path(f.name)
            
            # Output path for combined audio
            combined_path = output_dir / "combined_audio.wav"
            
            # FFmpeg command to concatenate WAV files
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_list),
                '-c', 'copy',
                str(combined_path)
            ]
            
            logger.info("Combining audio segments...")
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Clean up temporary file
            concat_list.unlink()
            
            return combined_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error combining segments: {e.stderr.decode()}")
            raise
        except Exception as e:
            logger.error(f"Error combining audio segments: {str(e)}")
            raise
    
    def _upload_to_gemini(self, file_path: Path, retry_count: int = 0) -> Dict:
        """
        Upload audio file to Gemini with retry logic
        
        Args:
            file_path (Path): Path to audio file
            retry_count (int): Current retry attempt
            
        Returns:
            Dict: Gemini file response
        """
        try:
            with open(file_path, 'rb') as f:
                return genai.upload_file(f, mime_type="audio/wav")
        except Exception as e:
            if retry_count < self.max_retries:
                logger.warning(f"Retry {retry_count + 1} for {file_path}")
                time.sleep(2 ** retry_count)  # Exponential backoff
                return self._upload_to_gemini(file_path, retry_count + 1)
            else:
                logger.error(f"Failed to upload {file_path} after {self.max_retries} attempts")
                raise
    
    def _process_audio(self, file_path: Path) -> str:
        """Process audio file with Gemini"""
        try:
            # Upload file to Gemini
            file = self._upload_to_gemini(file_path)
            
            # Get format-specific prompt
            prompt = self.formatter.get_prompt()
            
            # Create chat session with context
            chat = self.model.start_chat(history=[{
                "role": "user",
                "parts": [file, prompt]
            }])
            
            # Get transcription
            response = chat.send_message(
                "Process the audio and format the output as specified. "
                "Ensure accurate speaker identification and timestamp precision."
            )
            
            # Format the response
            return self.formatter.format_output(response.text)
            
        except Exception as e:
            logger.error(f"Error processing audio {file_path}: {str(e)}")
            raise
    
    def transcribe(self, segment_paths: List[Path], output_dir: Path) -> Path:
        """Transcribe and diarize audio segments"""
        try:
            # Combine all segments into one file
            combined_audio = self._combine_audio_segments(segment_paths, output_dir)
            logger.info("Audio segments combined successfully")
            
            # Process the combined audio
            logger.info("Starting transcription of combined audio")
            transcription = self._process_audio(combined_audio)
            
            # Save transcription with appropriate extension
            extension = 'json' if isinstance(self.formatter, JsonFormatter) else 'txt'
            output_path = output_dir / f"transcription.{extension}"
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(transcription)
            
            logger.info(f"Transcription completed and saved to {output_path}")
            
            # Clean up combined audio file
            combined_audio.unlink()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise 