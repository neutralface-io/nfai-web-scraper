from abc import ABC, abstractmethod
from typing import List, Dict, Literal
import json
import re

TimeUnit = Literal['ms', 's', 'min']

class BaseFormatter(ABC):
    """Base class for output formatters"""
    
    def __init__(self, time_unit: TimeUnit = 'ms'):
        """
        Initialize formatter with time unit
        
        Args:
            time_unit (TimeUnit): Time unit for timestamps ('ms', 's', or 'min')
        """
        self.time_unit = time_unit
        self._conversion_factors = {
            'ms': 1,
            's': 1000,
            'min': 60000
        }
    
    def _convert_time(self, ms: int) -> float:
        """Convert milliseconds to specified time unit"""
        factor = self._conversion_factors[self.time_unit]
        return ms / factor
    
    def _parse_time(self, value: str) -> int:
        """Parse time value to milliseconds"""
        try:
            return int(float(value) * self._conversion_factors[self.time_unit])
        except (ValueError, TypeError):
            return 0
    
    @abstractmethod
    def get_prompt(self) -> str:
        """Get format-specific Gemini prompt"""
        pass
    
    @abstractmethod
    def format_output(self, text: str) -> str:
        """Format the transcription output"""
        pass

class TextFormatter(BaseFormatter):
    """Format output as semicolon-delimited text"""
    
    def get_prompt(self) -> str:
        unit_examples = {
            'ms': '1500 for 1.5 seconds',
            's': '1.5 for 1.5 seconds',
            'min': '0.025 for 1.5 seconds'
        }
        return (
            "Generate audio diarization with transcriptions and speaker information. "
            f"Include timestamps in {self.time_unit} (e.g., {unit_examples[self.time_unit]}). "
            f"Format each line as: <timestamp_{self.time_unit}>;<speaker_name>;<transcription> "
            "Output should be compact with no blank lines between entries. "
            "Each entry should be on a new line without extra spacing."
        )
    
    def format_output(self, text: str) -> str:
        # Clean up and convert timestamps if needed
        formatted_lines = []
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                timestamp, speaker, transcription = [x.strip() for x in line.split(';', 2)]
                ms = self._parse_time(timestamp)
                converted_time = self._convert_time(ms)
                formatted_lines.append(f"{converted_time};{speaker};{transcription}")
            except (ValueError, IndexError):
                continue
        return '\n'.join(formatted_lines)

class JsonFormatter(BaseFormatter):
    """Format output as structured JSON"""
    
    def get_prompt(self) -> str:
        unit_examples = {
            'ms': '1500 for 1.5 seconds',
            's': '1.5 for 1.5 seconds',
            'min': '0.025 for 1.5 seconds'
        }
        return (
            "Generate audio diarization with transcriptions and speaker information. "
            f"Include timestamps in {self.time_unit} (e.g., {unit_examples[self.time_unit]}). "
            "For each speech segment, provide: "
            f"- timestamp_{self.time_unit} "
            "- speaker name (inferred from audio) "
            "- transcription text "
            "Format as a simple list with each entry on a new line: "
            f"timestamp_{self.time_unit} | speaker | transcription"
        )
    
    def format_output(self, text: str) -> str:
        entries = []
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                timestamp, speaker, transcription = [x.strip() for x in line.split('|', 2)]
                ms = self._parse_time(timestamp)
                entries.append({
                    f'timestamp_{self.time_unit}': self._convert_time(ms),
                    'speaker': speaker,
                    'transcription': transcription
                })
            except (ValueError, IndexError):
                continue
        
        return json.dumps({'segments': entries}, indent=2, ensure_ascii=False)

def get_formatter(format_type: str, time_unit: TimeUnit = 'ms') -> BaseFormatter:
    """
    Factory function to get appropriate formatter
    
    Args:
        format_type (str): Output format type ('txt' or 'json')
        time_unit (TimeUnit): Time unit for timestamps ('ms', 's', or 'min')
    """
    formatters = {
        'txt': TextFormatter(time_unit),
        'json': JsonFormatter(time_unit)
    }
    return formatters.get(format_type.lower(), TextFormatter(time_unit)) 