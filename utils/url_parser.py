import re
from urllib.parse import urlparse, parse_qs

def extract_video_id(url: str) -> str:
    """
    Extract video ID from various platform URLs
    
    Args:
        url (str): Video URL from supported platforms
        
    Returns:
        str: Video identifier
    """
    parsed = urlparse(url)
    
    # YouTube
    if 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc:
        if 'youtu.be' in parsed.netloc:
            return parsed.path.strip('/')
        if 'watch' in parsed.path:
            return parse_qs(parsed.query)['v'][0]
            
    # Twitch
    if 'twitch.tv' in parsed.netloc:
        if 'clips' in parsed.netloc or 'clip' in parsed.path:
            return parsed.path.split('/')[-1]
        if 'videos' in parsed.path:
            return re.search(r'/videos/(\d+)', parsed.path).group(1)
    
    # If no ID found, use the last path segment
    path_segments = [s for s in parsed.path.split('/') if s]
    return path_segments[-1] if path_segments else 'unknown' 