from abc import ABC, abstractmethod
from typing import List, Dict
import json

class BaseFormatter(ABC):
    """Base class for output formatters"""
    
    def _format_timestamp(self, seconds: float) -> str:
        """
        Convert seconds to HH:MM:SS.mmm format
        Handles elapsed time in a video/audio context
        
        Args:
            seconds (float): Time in seconds
            
        Returns:
            str: Formatted timestamp (HH:MM:SS.mmm)
        """
        # Convert to total milliseconds first
        total_ms = int(float(seconds) * 1000)
        
        # Calculate each component
        ms = total_ms % 1000
        total_seconds = total_ms // 1000
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"
    
    @abstractmethod
    def get_prompt(self) -> str:
        """Get format-specific Gemini prompt"""
        pass
    
    @abstractmethod
    def format_output(self, text: str) -> str:
        """Format the transcription output"""
        pass

class TextFormatter(BaseFormatter):
    """Format output as semicolon-delimited text with HH:MM:SS.mmm timestamps"""
    
    def get_prompt(self) -> str:
        return (
            "Generate audio diarization with transcriptions and speaker information. "
            "Include precise timestamps in seconds (with decimals for milliseconds). "
            "Format each line as: <timestamp>;<speaker_name>;<transcription> "
            "Output should be compact with no blank lines between entries. "
            "Each entry should be on a new line without extra spacing. "
            "Timestamps should reflect the exact time in the audio when each segment starts."
        )
    
    def format_output(self, text: str) -> str:
        formatted_lines = []
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                timestamp, speaker, transcription = [x.strip() for x in line.split(';', 2)]
                time_str = self._format_timestamp(timestamp)
                formatted_lines.append(f"{time_str};{speaker};{transcription}")
            except (ValueError, IndexError):
                continue
        return '\n'.join(formatted_lines)

class JsonFormatter(BaseFormatter):
    """Format output as structured JSON with HH:MM:SS.mmm timestamps"""
    
    def get_prompt(self) -> str:
        return (
            "Generate audio diarization with transcriptions and speaker information. "
            "Include precise timestamps in seconds (with decimals for milliseconds). "
            "For each speech segment, provide: "
            "- exact timestamp when the segment starts in the audio "
            "- speaker name (inferred from audio) "
            "- transcription text "
            "Format as a simple list with each entry on a new line: "
            "timestamp | speaker | transcription"
        )
    
    def format_output(self, text: str) -> str:
        entries = []
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                timestamp, speaker, transcription = [x.strip() for x in line.split('|', 2)]
                time_str = self._format_timestamp(timestamp)
                entries.append({
                    'timestamp': time_str,
                    'speaker': speaker,
                    'transcription': transcription
                })
            except (ValueError, IndexError):
                continue
        
        return json.dumps({'segments': entries}, separators=(',', ':'))  # Compact JSON

def get_formatter(format_type: str) -> BaseFormatter:
    """Factory function to get appropriate formatter"""
    formatters = {
        'txt': TextFormatter(),
        'json': JsonFormatter()
    }
    return formatters.get(format_type.lower(), TextFormatter()) 