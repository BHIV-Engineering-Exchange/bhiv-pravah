
import requests
from typing import List, Optional
from app.core.config import settings
from app.schemas.chat import YouTubeVideo

async def get_youtube_recommendations(subject: str, topic: str, max_results: int = 5) -> List[YouTubeVideo]:
    """Get YouTube video recommendations based on subject and topic"""
    if not settings.YOUTUBE_API_KEY:
        return []  # Return empty list if API key is not configured
    
    # Create search query
    search_query = f"{subject} {topic} tutorial explanation"
    
    params = {
        "part": "snippet",
        "q": search_query,
        "type": "video",
        "maxResults": max_results,
        "key": settings.YOUTUBE_API_KEY,
        "order": "relevance",
        "videoCategoryId": "27",  # Education category
        "safeSearch": "strict"
    }
    
    try:
        response = requests.get(settings.YOUTUBE_API_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        videos = []
        for item in data.get("items", []):
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]
            
            video = YouTubeVideo(
                title=snippet["title"],
                video_id=video_id,
                url=f"https://www.youtube.com/watch?v={video_id}",
                thumbnail=snippet["thumbnails"]["high"]["url"],
                channel_title=snippet["channelTitle"]
            )
            videos.append(video)
        
        return videos
    except Exception as e:
        print(f"Error fetching YouTube recommendations: {str(e)}")
        return []
