import logging
import google.generativeai as genai
from pathlib import Path
from typing import Dict, Optional
import time
from io import BytesIO

logger = logging.getLogger(__name__)

class GeminiProvider:
    """Provider for Gemini AI transcription and diarization"""
    
    def __init__(self, api_key: str, model_name: str = 'gemini-1.5-flash', max_retries: int = 3):
        """
        Initialize Gemini provider
        
        Args:
            api_key (str): Gemini API key
            model_name (str): Name of the Gemini model to use
            max_retries (int): Maximum number of retry attempts
        """
        self.max_retries = max_retries
        self.model_name = model_name
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def _upload_file(self, file_path: Path, retry_count: int = 0) -> Optional[Dict]:
        """
        Upload file to Gemini with retry logic
        
        Args:
            file_path (Path): Path to audio file
            retry_count (int): Current retry attempt
            
        Returns:
            Dict: Gemini file response or None on failure
        """
        try:
            with open(file_path, 'rb') as f:
                return genai.upload_file(f, mime_type="audio/wav")
        except Exception as e:
            if retry_count < self.max_retries:
                logger.warning(f"Retry {retry_count + 1} for {file_path}")
                time.sleep(2 ** retry_count)  # Exponential backoff
                return self._upload_file(file_path, retry_count + 1)
            else:
                logger.error(f"Failed to upload {file_path} after {self.max_retries} attempts: {str(e)}")
                return None
    
    def transcribe(self, audio_path: Path, prompt: str) -> Optional[str]:
        """
        Transcribe audio file using Gemini
        
        Args:
            audio_path (Path): Path to audio file
            prompt (str): Instruction prompt for transcription
            
        Returns:
            str: Transcribed text or None on failure
        """
        try:
            # Upload file
            file = self._upload_file(audio_path)
            if not file:
                raise ValueError(f"Failed to upload file: {audio_path}")
            
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
            
            return response.text
            
        except Exception as e:
            logger.error(f"Transcription failed for {audio_path}: {str(e)}")
            return None
    
    def _upload_bytes(self, audio_data: bytes, retry_count: int = 0) -> Optional[Dict]:
        """
        Upload bytes data to Gemini with retry logic
        
        Args:
            audio_data (bytes): Audio data in WAV format
            retry_count (int): Current retry attempt
            
        Returns:
            Dict: Gemini file response or None on failure
        """
        try:
            # Convert bytes to file-like object
            audio_file = BytesIO(audio_data)
            audio_file.name = "audio.wav"  # Required for mime-type detection
            return genai.upload_file(audio_file, mime_type="audio/wav")
        except Exception as e:
            if retry_count < self.max_retries:
                logger.warning(f"Retry {retry_count + 1} for audio upload")
                time.sleep(2 ** retry_count)  # Exponential backoff
                return self._upload_bytes(audio_data, retry_count + 1)
            else:
                logger.error(f"Failed to upload audio data after {self.max_retries} attempts: {str(e)}")
                return None
    
    def transcribe_bytes(self, audio_data: bytes, prompt: str) -> Optional[str]:
        """
        Transcribe audio data using Gemini
        
        Args:
            audio_data (bytes): Raw audio data in WAV format
            prompt (str): Instruction prompt for transcription
            
        Returns:
            str: Transcribed text or None on failure
        """
        try:
            # Upload audio data
            file = self._upload_bytes(audio_data)
            if not file:
                raise ValueError("Failed to upload audio data")
            
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
            
            return response.text
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return None
    
    @property
    def name(self) -> str:
        """Get provider name"""
        return "Gemini"
    
    @property
    def version(self) -> str:
        """Get model version"""
        return self.model_name
