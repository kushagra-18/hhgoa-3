import logging
from typing import List, Optional
import requests

from src.config import settings
from src.search.social_parser import DiscoveredPost, SocialPostParser
from src.search.providers.base import BaseSearchProvider

logger = logging.getLogger("search_provider.serpapi")


class SerpApiLensProvider(BaseSearchProvider):
    """Google Lens Reverse Image Search via SerpApi."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SERPAPI_API_KEY

    def search(self, image_path: str, image_bytes: Optional[bytes] = None) -> List[DiscoveredPost]:
        if not self.api_key:
            return []

        try:
            logger.info("Executing Google Lens search via SerpApi...")
            url = "https://serpapi.com/search"
            
            with open(image_path, "rb") as f:
                files = {"image": f}
                params = {
                    "engine": "google_lens",
                    "api_key": self.api_key,
                }
                response = requests.post(url, params=params, files=files, timeout=20)
            
            if response.status_code != 200:
                logger.warning(f"SerpApi error: {response.status_code} - {response.text}")
                return []

            data = response.json()
            matches = []
            
            visual_matches = data.get("visual_matches", [])
            for item in visual_matches[:5]:
                post_url = item.get("link", "")
                title = item.get("title", "")
                source = item.get("source", "")
                thumbnail = item.get("thumbnail", "")
                
                if post_url:
                    post = SocialPostParser.extract_from_raw(
                        url=post_url,
                        title=title,
                        snippet=f"{title} - Discovered via {source}",
                        image_url=thumbnail,
                        author=source,
                        raw_meta=item,
                    )
                    matches.append(post)
                    
            return matches
        except Exception as e:
            logger.error(f"SerpApi search failed: {e}")
            return []
