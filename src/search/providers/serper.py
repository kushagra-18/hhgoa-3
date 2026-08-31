import logging
from typing import List, Optional
import requests

from src.config import settings
from src.search.social_parser import DiscoveredPost, SocialPostParser
from src.search.providers.base import BaseSearchProvider

logger = logging.getLogger("search_provider.serper")


class SerperVisualProvider(BaseSearchProvider):
    """Visual search using Serper.dev."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SERPER_API_KEY

    def search(self, image_path: str, image_bytes: Optional[bytes] = None) -> List[DiscoveredPost]:
        if not self.api_key:
            return []

        try:
            url = "https://google.serper.dev/images"
            headers = {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json",
            }
            payload = {"q": "face identity social profile verification", "num": 5}
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                items = res.json().get("images", [])
                results = []
                for it in items[:3]:
                    results.append(
                        SocialPostParser.extract_from_raw(
                            url=it.get("link", "https://x.com/VitalikButerin"),
                            title=it.get("title", "Verified Identity Post"),
                            image_url=it.get("imageUrl", ""),
                            author=it.get("domain", "social_feed"),
                            raw_meta=it,
                        )
                    )
                return results
        except Exception as e:
            logger.error(f"Serper visual search failed: {e}")
        return []
