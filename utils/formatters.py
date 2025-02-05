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
    """Format output as semicolon-delimited text with nanosecond timestamps"""
    
    def get_prompt(self) -> str:
        return (
            "Generate audio diarization with transcriptions and speaker information. "
            "Include timestamps in seconds with up to 9 decimal places. "
            "Format each line as: <timestamp>;<speaker_name>;<transcription> "
            "Output should be compact with no blank lines between entries. "
            "Each entry should be on a new line without extra spacing."
        )
    
    def format_output(self, text: str) -> str:
        # Convert seconds to nanoseconds and format as integer
        formatted_lines = []
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                timestamp, speaker, transcription = [x.strip() for x in line.split(';', 2)]
                # Convert to nanoseconds (1 second = 1_000_000_000 nanoseconds)
                ns = int(float(timestamp) * 1_000_000_000)
                formatted_lines.append(f"{ns};{speaker};{transcription}")
            except (ValueError, IndexError):
                continue
        return '\n'.join(formatted_lines)

class JsonFormatter(BaseFormatter):
    """Format output as structured JSON with nanosecond timestamps"""
    
    def get_prompt(self) -> str:
        return (
            "Generate audio diarization with transcriptions and speaker information. "
            "Include timestamps in seconds with up to 9 decimal places. "
            "For each speech segment, provide: "
            "- timestamp in seconds "
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
                # Convert to nanoseconds
                ns = int(float(timestamp) * 1_000_000_000)
                entries.append({
                    'timestamp': ns,  # Using 'ns' for compact key name
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