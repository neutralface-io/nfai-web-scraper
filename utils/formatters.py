from abc import ABC, abstractmethod
from typing import List, Dict
import json

class BaseFormatter(ABC):
    """Base class for output formatters"""
    
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
            "Format each line as: <timestamp>;<speaker_name>;<transcription>\n"
            "Timestamps must be in HH:MM:SS.mmm format (e.g., 00:01:23.456). "
            "Hours, minutes, and seconds should increment properly (e.g., 01:00:00.000 for 1 hour). "
            "Output should be compact with no blank lines between entries.\n"
            "Example format:\n"
            "00:00:00.000;Speaker 1;Hello everyone\n"
            "00:00:02.500;Speaker 2;Hi there\n"
            "01:30:45.100;Speaker 1;Let's continue"
        )
    
    def format_output(self, text: str) -> str:
        # Just clean up whitespace and filter empty lines
        return '\n'.join(line.strip() for line in text.splitlines() if line.strip())

class JsonFormatter(BaseFormatter):
    """Format output as structured JSON with HH:MM:SS.mmm timestamps"""
    
    def get_prompt(self) -> str:
        return (
            "Generate audio diarization with transcriptions and speaker information. "
            "For each speech segment, provide timestamp, speaker name, and transcription. "
            "Timestamps must be in HH:MM:SS.mmm format (e.g., 00:01:23.456). "
            "Hours, minutes, and seconds should increment properly (e.g., 01:00:00.000 for 1 hour). "
            "Format as: timestamp | speaker | transcription\n"
            "Example format:\n"
            "00:00:00.000 | Speaker 1 | Hello everyone\n"
            "00:00:02.500 | Speaker 2 | Hi there\n"
            "01:30:45.100 | Speaker 1 | Let's continue"
        )
    
    def format_output(self, text: str) -> str:
        entries = []
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                timestamp, speaker, transcription = [x.strip() for x in line.split('|', 2)]
                entries.append({
                    'timestamp': timestamp,
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