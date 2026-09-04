import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from urllib.parse import urlparse


@dataclass
class DiscoveredPost:
    """Standardized representation of a discovered web or social media post."""
    platform: str # "Twitter/X", "LinkedIn", "Instagram", "Reddit", "Web"
    post_url: str
    author_handle: str
    author_name: str
    post_caption: str
    post_timestamp: str
    post_image_url: str
    post_image_sha256: str = ""
    visual_similarity_score: float = 0.0
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def canonical_dict(self) -> Dict[str, Any]:
        """
        Deterministic, key-sorted dictionary representation used for cryptographic
        fingerprinting and on-chain tamper verification.
        """
        return {
            "author_handle": self.author_handle.strip(),
            "author_name": self.author_name.strip(),
            "platform": self.platform.strip(),
            "post_caption": self.post_caption.strip(),
            "post_image_sha256": self.post_image_sha256.strip(),
            "post_image_url": self.post_image_url.strip(),
            "post_timestamp": self.post_timestamp.strip(),
            "post_url": self.post_url.strip(),
        }

    def canonical_json(self) -> str:
        """Returns sorted, compact JSON string for hashing."""
        return json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":"))

    def compute_payload_hash(self) -> str:
        """Compute SHA-256 / Keccak-256 hash of the canonical post data."""
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["payload_hash"] = self.compute_payload_hash()
        data["top_candidates"] = self.raw_metadata.get("top_candidates", [])
        return data


class SocialPostParser:
    """Parses URLs and html/api responses into standardized DiscoveredPost objects."""

    @staticmethod
    def detect_platform(url: str) -> str:
        domain = urlparse(url).netloc.lower()
        if "twitter.com" in domain or "x.com" in domain:
            return "Twitter/X"
        elif "linkedin.com" in domain:
            return "LinkedIn"
        elif "instagram.com" in domain:
            return "Instagram"
        elif "facebook.com" in domain or "fb.com" in domain or "fb.watch" in domain:
            return "Facebook"
        elif "youtube.com" in domain or "youtu.be" in domain:
            return "YouTube"
        elif "tiktok.com" in domain or "douyin.com" in domain:
            return "TikTok"
        elif "reddit.com" in domain:
            return "Reddit"
        elif "pinterest.com" in domain:
            return "Pinterest"
        elif "threads.net" in domain:
            return "Threads"
        elif "snapchat.com" in domain:
            return "Snapchat"
        elif "t.me" in domain or "telegram.org" in domain:
            return "Telegram"
        elif "whatsapp.com" in domain or "wa.me" in domain:
            return "WhatsApp"
        elif "vk.com" in domain or "vkontakte.ru" in domain:
            return "VK"
        elif "github.com" in domain:
            return "GitHub"
        elif "gitlab.com" in domain:
            return "GitLab"
        elif "medium.com" in domain:
            return "Medium"
        elif "tumblr.com" in domain:
            return "Tumblr"
        elif "bsky.app" in domain or "bsky.social" in domain:
            return "Bluesky"
        elif "mastodon" in domain:
            return "Mastodon"
        elif "discord.com" in domain or "discord.gg" in domain:
            return "Discord"
        elif "twitch.tv" in domain:
            return "Twitch"
        elif "quora.com" in domain:
            return "Quora"
        elif "wechat.com" in domain or "weixin.qq.com" in domain:
            return "WeChat"
        elif "weibo.com" in domain or "weibo.cn" in domain:
            return "Weibo"
        elif "xiaohongshu.com" in domain:
            return "Xiaohongshu"
        elif "bilibili.com" in domain:
            return "Bilibili"
        elif "doximity.com" in domain:
            return "Doximity"
        elif "researchgate.net" in domain:
            return "ResearchGate"
        elif "orcid.org" in domain:
            return "ORCID"
        elif "wikipedia.org" in domain:
            return "Wikipedia"
        return "Web"

    @staticmethod
    def extract_from_raw(
        url: str,
        title: str = "",
        snippet: str = "",
        image_url: str = "",
        author: str = "",
        timestamp: str = "",
        raw_meta: Optional[Dict[str, Any]] = None,
    ) -> DiscoveredPost:
        platform = SocialPostParser.detect_platform(url)
        author_name = author or "Identified Public Profile"
        author_handle = f"@{author_name.lower().replace(' ', '_')}"
        
        caption = snippet or title or "Social media post matching facial scan."
        ts = timestamp or "2024-05-18T14:30:00Z"
        
        return DiscoveredPost(
            platform=platform,
            post_url=url,
            author_handle=author_handle,
            author_name=author_name,
            post_caption=caption,
            post_timestamp=ts,
            post_image_url=image_url,
            raw_metadata=raw_meta or {},
        )
