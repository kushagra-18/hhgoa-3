import io
import logging
from typing import List, Optional
from PIL import Image
import requests

from src.config import settings
from src.search.social_parser import DiscoveredPost, SocialPostParser
from src.search.providers.base import BaseSearchProvider

logger = logging.getLogger("search_provider.serpapi")


class SerpApiLensProvider(BaseSearchProvider):
    """Google Lens Reverse Image Search via SerpApi."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SERPAPI_API_KEY

    def _prepare_image_bytes(self, image_path: str, image_bytes: Optional[bytes] = None) -> bytes:
        """Ensure image bytes are within SerpApi 500KB limit."""
        if not image_bytes:
            with open(image_path, "rb") as f:
                image_bytes = f.read()

        if len(image_bytes) > 480_000:
            try:
                img = Image.open(io.BytesIO(image_bytes))
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.thumbnail((800, 800))
                out_buf = io.BytesIO()
                img.save(out_buf, format="JPEG", quality=85)
                return out_buf.getvalue()
            except Exception as e:
                logger.warning(f"Failed to resize image for SerpApi: {e}")
                return image_bytes
        return image_bytes

    def search(
        self,
        image_path: str,
        image_bytes: Optional[bytes] = None,
        top_n: int = 15,
    ) -> List[DiscoveredPost]:
        if not self.api_key:
            logger.info("SerpApi API key not configured, skipping SerpApi search.")
            return []

        try:
            logger.info("Executing Google Lens search via SerpApi...")
            upload_bytes = self._prepare_image_bytes(image_path, image_bytes)

            # Step 1: Upload image to SerpApi
            upload_url = "https://serpapi.com/image"
            upload_files = {"image": ("face_scan.jpg", upload_bytes, "image/jpeg")}
            upload_data = {"api_key": self.api_key}

            upload_res = requests.post(
                upload_url,
                files=upload_files,
                data=upload_data,
                timeout=20,
            )

            if upload_res.status_code != 200:
                logger.warning(f"SerpApi image upload failed ({upload_res.status_code}): {upload_res.text}")
                return []

            image_id = upload_res.json().get("image_id")
            if not image_id:
                logger.warning("No image_id returned from SerpApi upload.")
                return []

            # Step 2: Query Google Lens with image_id
            search_url = "https://serpapi.com/search"
            search_params = {
                "engine": "google_lens",
                "image_id": image_id,
                "api_key": self.api_key,
            }
            search_res = requests.get(search_url, params=search_params, timeout=25)

            if search_res.status_code != 200:
                logger.warning(f"SerpApi Google Lens search failed ({search_res.status_code}): {search_res.text}")
                return []

            data = search_res.json()
            if getattr(settings, "APP_ENV", "").lower() in ("dev", "development"):
                import json
                from datetime import datetime
                json_str = json.dumps(data, indent=2)
                print(f"[DEV] SerpApi Google Lens Response JSON:\n{json_str}", flush=True)
                logger.info(f"SerpApi Google Lens Response JSON:\n{json_str}")
                try:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    debug_file = settings.DATA_DIR / f"serpapi_response_{ts}.json"
                    latest_file = settings.DATA_DIR / "serpapi_response_latest.json"
                    with open(debug_file, "w", encoding="utf-8") as df:
                        df.write(json_str)
                    with open(latest_file, "w", encoding="utf-8") as lf:
                        lf.write(json_str)
                    logger.info(f"Saved SerpApi response to {debug_file.name} and {latest_file.name}")
                except Exception as e:
                    logger.debug(f"Could not write serpapi debug json: {e}")

            visual_matches = data.get("visual_matches", [])
            logger.info(f"SerpApi Google Lens found {len(visual_matches)} visual matches.")

            matches: List[DiscoveredPost] = []
            for item in visual_matches[:top_n]:
                post_url = item.get("link", "")
                title = item.get("title", "")
                source = item.get("source", "")
                thumbnail = item.get("thumbnail", "")

                if post_url or thumbnail:
                    post = SocialPostParser.extract_from_raw(
                        url=post_url,
                        title=title,
                        snippet=f"{title} - Discovered via {source}",
                        image_url=thumbnail,
                        author=source or title,
                        raw_meta=item,
                    )
                    matches.append(post)

            return matches

        except Exception as e:
            logger.error(f"SerpApi Google Lens search error: {e}")
            return []


class SerpApiYandexProvider(BaseSearchProvider):
    """Yandex Reverse Image Search via SerpApi (engine=yandex_images)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SERPAPI_API_KEY

    def _get_public_image_url(self, image_path: str, image_bytes: Optional[bytes] = None) -> Optional[str]:
        """Upload image to a fast anonymous host to get a public URL for Yandex."""
        if image_path.startswith("http://") or image_path.startswith("https://"):
            return image_path

        if not image_bytes:
            try:
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
            except Exception as e:
                logger.warning(f"Could not read image file for Yandex upload: {e}")
                return None

        # Attempt 1: freeimage.host (Generates direct iili.io public image CDN link that Yandex reliably accesses)
        try:
            r = requests.post(
                "https://freeimage.host/api/1/upload",
                data={"key": "6d207e02198a847aa98d0a2a901485a5", "action": "upload"},
                files={"source": ("face_scan.jpg", image_bytes, "image/jpeg")},
                timeout=12,
            )
            if r.status_code == 200:
                direct_url = r.json().get("image", {}).get("url", "")
                if direct_url and direct_url.startswith("http"):
                    return direct_url.strip()
        except Exception as e:
            logger.debug(f"FreeImage upload failed: {e}")

        # Attempt 2: catbox.moe (Direct files.catbox.moe CDN link with browser UA)
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
            r = requests.post(
                "https://catbox.moe/user/api.php",
                headers=headers,
                data={"reqtype": "fileupload"},
                files={"fileToUpload": ("face_scan.jpg", image_bytes, "image/jpeg")},
                timeout=12,
            )
            if r.status_code == 200 and r.text.startswith("http"):
                return r.text.strip()
        except Exception as e:
            logger.debug(f"Catbox upload failed: {e}")

        return None

    def search(
        self,
        image_path: str,
        image_bytes: Optional[bytes] = None,
        top_n: int = 15,
    ) -> List[DiscoveredPost]:
        if not self.api_key:
            logger.info("SerpApi API key not configured, skipping Yandex search.")
            return []

        try:
            logger.info("Executing Yandex Reverse Image search via SerpApi...")
            public_url = self._get_public_image_url(image_path, image_bytes)
            if not public_url:
                logger.warning("Could not establish public image URL for Yandex search.")
                return []

            search_url = "https://serpapi.com/search"
            search_params = {
                "engine": "yandex_images",
                "url": public_url,
                "api_key": self.api_key,
            }
            search_res = requests.get(search_url, params=search_params, timeout=30)
            if search_res.status_code != 200:
                logger.warning(f"SerpApi Yandex search failed ({search_res.status_code}): {search_res.text}")
                return []

            data = search_res.json()
            if getattr(settings, "APP_ENV", "").lower() in ("dev", "development"):
                import json
                try:
                    debug_file = settings.DATA_DIR / "serpapi_yandex_response_latest.json"
                    with open(debug_file, "w", encoding="utf-8") as df:
                        json.dump(data, df, indent=2)
                except Exception:
                    pass

            image_results = data.get("image_results", [])
            similar_images = data.get("similar_images", [])
            logger.info(
                f"SerpApi Yandex found {len(image_results)} image results and {len(similar_images)} similar images."
            )

            matches: List[DiscoveredPost] = []
            for item in image_results[:top_n]:
                link = item.get("link", "")
                title = item.get("title", "")
                source = item.get("source", "")
                snippet = item.get("snippet", "") or title

                thumb_obj = item.get("thumbnail")
                thumb_url = thumb_obj.get("link", "") if isinstance(thumb_obj, dict) else (thumb_obj or "")
                orig_url = item.get("original_image", "") or thumb_url
                img_url = thumb_url or orig_url

                if link or img_url:
                    post = SocialPostParser.extract_from_raw(
                        url=link,
                        title=title,
                        snippet=snippet,
                        image_url=img_url,
                        author=source or title,
                        raw_meta={"source_engine": "yandex_images", **item},
                    )
                    matches.append(post)

            # Also incorporate similar images if matches list is small
            if len(matches) < top_n and similar_images:
                for sim in similar_images[: top_n - len(matches)]:
                    sim_link = sim.get("link", "")
                    sim_img = sim.get("image", "")
                    if sim_link or sim_img:
                        post = SocialPostParser.extract_from_raw(
                            url=sim_link,
                            title="Visually Similar Image",
                            snippet="Similar face found on Yandex",
                            image_url=sim_img,
                            author="Yandex Match",
                            raw_meta={"source_engine": "yandex_images_similar", **sim},
                        )
                        matches.append(post)

            return matches

        except Exception as e:
            logger.error(f"SerpApi Yandex search error: {e}")
            return []
