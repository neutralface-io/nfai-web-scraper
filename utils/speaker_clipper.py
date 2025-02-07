import logging
from pathlib import Path
from typing import Dict, List
import json
import subprocess

logger = logging.getLogger(__name__)

class SpeakerClipper:
    """Handles extraction of speaker-specific audio clips"""
    
    def __init__(self, clip_duration: int = 30):
        """
        Initialize speaker clipper
        
        Args:
            clip_duration: Duration of clips in seconds
        """
        self.clip_duration = clip_duration
    
    def extract_speaker_clips(self, audio_path: Path, segments: List[Dict], output_dir: Path) -> Dict[str, Path]:
        """
        Extract audio clips for each speaker from the processed audio
        
        Args:
            audio_path: Path to processed audio file
            segments: List of transcription segments
            output_dir: Directory to save speaker clips
            
        Returns:
            Dict mapping speaker IDs to clip paths
        """
        try:
            # Find best segments for each speaker
            best_segments = self._find_best_segments(segments)
            
            # Create speaker clips directory
            clips_dir = output_dir / 'speaker_clips'
            clips_dir.mkdir(exist_ok=True)
            
            # Extract clips for each speaker
            speaker_clips = {}
            for speaker, timestamp in best_segments.items():
                clip_path = self._extract_clip(
                    audio_path,
                    clips_dir / f"{speaker.lower().replace(' ', '_')}.wav",
                    timestamp
                )
                speaker_clips[speaker] = clip_path
            
            return speaker_clips
            
        except Exception as e:
            logger.error(f"Failed to extract speaker clips: {str(e)}")
            raise
    
    def _find_best_segments(self, segments: List[Dict]) -> Dict[str, str]:
        """Find longest segment for each speaker"""
        speaker_segments = {}
        
        for segment in segments:
            speaker = segment['speaker']
            duration = self._parse_duration(segment.get('duration', '0'))
            
            if speaker not in speaker_segments or duration > speaker_segments[speaker]['duration']:
                speaker_segments[speaker] = {
                    'timestamp': segment['timestamp'],
                    'duration': duration
                }
        
        return {
            speaker: data['timestamp']
            for speaker, data in speaker_segments.items()
        }
    
    def _extract_clip(self, audio_path: Path, output_path: Path, start_time: str) -> Path:
        """Extract audio clip starting at timestamp"""
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', str(audio_path),
                '-ss', start_time,
                '-t', str(self.clip_duration),
                '-c:a', 'pcm_s16le',  # WAV format
                '-ar', '48000',       # 48kHz sample rate
                '-ac', '1',           # Mono
                str(output_path)
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise
    
    def _parse_duration(self, timestamp: str) -> float:
        """Convert HH:MM:SS.mmm to seconds"""
        try:
            h, m, s = timestamp.split(':')
            return float(h) * 3600 + float(m) * 60 + float(s)
        except:
            return 0.0 