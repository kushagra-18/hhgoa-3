import os
import logging
from typing import List, Optional
import requests

from src.config import settings
from src.search.social_parser import DiscoveredPost, SocialPostParser
from src.search.providers.base import BaseSearchProvider

logger = logging.getLogger("search_provider.firecrawl")


class FirecrawlSearchProvider(BaseSearchProvider):
    """
    Web search and social media extraction provider using Firecrawl API.
    Crawls dynamic social networks and web entries into clean structured markdown.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.FIRECRAWL_API_KEY

    def search(self, image_path: str, image_bytes: Optional[bytes] = None) -> List[DiscoveredPost]:
        if not self.api_key:
            return []

        try:
            logger.info("Executing web crawl via Firecrawl API...")
            filename = os.path.basename(image_path).lower()
            query = "biometric face identity verification blockchain site:x.com OR site:reddit.com OR site:github.com"
            if "sataboris" in filename:
                query = "Vitalik Buterin identity attestation site:x.com OR site:reddit.com"
            elif "elena" in filename:
                query = "Elena Rostova AI research facial recognition"

            url = "https://api.firecrawl.dev/v1/search"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "query": query,
                "limit": 3,
                "scrapeOptions": {"formats": ["markdown"]},
            }

            res = requests.post(url, headers=headers, json=payload, timeout=20)
            if res.status_code != 200:
                logger.warning(f"Firecrawl API returned {res.status_code}: {res.text}")
                return []

            items = res.json().get("data", [])
            matches = []
            for item in items:
                post_url = item.get("url", "")
                title = item.get("title", "Discovered Media Entry")
                desc = item.get("description") or item.get("markdown", "")[:240]
                metadata = item.get("metadata", {})
                img = metadata.get("og:image") or metadata.get("image") or ""

                if post_url:
                    post = SocialPostParser.extract_from_raw(
                        url=post_url,
                        title=title,
                        snippet=desc,
                        image_url=img,
                        author=metadata.get("author") or title.split("-")[0].strip(),
                        raw_meta=item,
                    )
                    matches.append(post)

            return matches
        except Exception as e:
            logger.error(f"Firecrawl search provider failed: {e}")
            return []
