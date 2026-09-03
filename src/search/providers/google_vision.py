import base64
import logging
from typing import List, Optional
import requests

from src.config import settings
from src.search.social_parser import DiscoveredPost, SocialPostParser
from src.search.providers.base import BaseSearchProvider

logger = logging.getLogger("search_provider.google_vision")


class GoogleCloudVisionProvider(BaseSearchProvider):
    """
    Reverse Image Search using Google Cloud Vision API (WEB_DETECTION).
    Provides 1,000 free requests per month.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "GOOGLE_VISION_API_KEY", "")

    def search(
        self,
        image_path: str,
        image_bytes: Optional[bytes] = None,
        top_n: int = 15,
    ) -> List[DiscoveredPost]:
        if not self.api_key:
            logger.debug("Google Cloud Vision API key not configured, skipping Google Vision search.")
            return []

        try:
            logger.info("Executing Google Cloud Vision Web Detection search...")
            if not image_bytes:
                with open(image_path, "rb") as f:
                    image_bytes = f.read()

            b64_content = base64.b64encode(image_bytes).decode("utf-8")

            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.api_key}"
            payload = {
                "requests": [
                    {
                        "image": {"content": b64_content},
                        "features": [{"type": "WEB_DETECTION", "maxResults": top_n}],
                    }
                ]
            }

            resp = requests.post(url, json=payload, timeout=20)
            if resp.status_code != 200:
                logger.warning(f"Google Cloud Vision API failed ({resp.status_code}): {resp.text}")
                return []

            data = resp.json()
            responses = data.get("responses", [])
            if not responses:
                return []

            web_detection = responses[0].get("webDetection", {})
            pages = web_detection.get("pagesWithMatchingImages", [])
            similar_images = web_detection.get("visuallySimilarImages", [])
            web_entities = web_detection.get("webEntities", [])

            top_entity_desc = ""
            for ent in web_entities:
                desc = ent.get("description", "").strip()
                if desc and len(desc) > 1:
                    top_entity_desc = desc
                    break

            matches: List[DiscoveredPost] = []

            for page in pages:
                page_url = page.get("url", "")
                page_title = page.get("pageTitle", "") or top_entity_desc or "Discovered Web Page"

                imgs = page.get("fullMatchingImages") or page.get("partialMatchingImages") or []
                img_url = imgs[0].get("url", "") if imgs else ""

                if page_url or img_url:
                    post = SocialPostParser.extract_from_raw(
                        url=page_url,
                        title=page_title,
                        snippet=f"{page_title} - Identified via Google Cloud Vision",
                        image_url=img_url,
                        author=top_entity_desc or page_title,
                        raw_meta={"source_engine": "google_cloud_vision", **page},
                    )
                    matches.append(post)

            if len(matches) < top_n and similar_images:
                for sim in similar_images[: top_n - len(matches)]:
                    sim_url = sim.get("url", "")
                    if sim_url:
                        post = SocialPostParser.extract_from_raw(
                            url=sim_url,
                            title=top_entity_desc or "Visually Similar Photo",
                            snippet="Similar image discovered via Google Cloud Vision",
                            image_url=sim_url,
                            author=top_entity_desc or "Web Discovery",
                            raw_meta={"source_engine": "google_cloud_vision_similar", **sim},
                        )
                        matches.append(post)

            logger.info(f"Google Cloud Vision found {len(matches)} matches.")
            return matches[:top_n]

        except Exception as e:
            logger.error(f"Google Cloud Vision search error: {e}")
            return []
