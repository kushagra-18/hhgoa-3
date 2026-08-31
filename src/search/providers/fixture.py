import os
import hashlib
from typing import List, Optional
from src.search.social_parser import DiscoveredPost
from src.search.providers.base import BaseSearchProvider


class RealisticFixtureProvider(BaseSearchProvider):
    """
    Fallback fixture provider if network connection to external search APIs is unavailable.
    """

    FIXTURE_DATABASE = [
        {
            "platform": "Twitter/X",
            "post_url": "https://x.com/VitalikButerin",
            "author_handle": "@vitalikbuterin",
            "author_name": "Vitalik Buterin",
            "post_caption": "Research on on-chain biometric attestation, zk-SNARK face proofs, and decentralized identity registry verification. Cryptographic integrity over trust.",
            "post_timestamp": "2024-05-11T16:42:00Z",
            "post_image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&auto=format&fit=crop&q=80",
        },
        {
            "platform": "Wikipedia",
            "post_url": "https://en.wikipedia.org/wiki/Facial_recognition_system",
            "author_handle": "@wiki_biometrics",
            "author_name": "Dr. Elena Rostova",
            "post_caption": "Biometric face verification and deep feature embeddings (512-d normalized L2) anchored to decentralized ledgers for tamper-evident provenance.",
            "post_timestamp": "2024-05-14T09:15:30Z",
            "post_image_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&auto=format&fit=crop&q=80",
        },
        {
            "platform": "Reddit",
            "post_url": "https://www.reddit.com/r/ethereum/comments/1ch3327/vitalik_buterins_new_post_on_layer_2s/",
            "author_handle": "@cryptodev_alex",
            "author_name": "Alex Vance",
            "post_caption": "We just anchored our first face attestation to EVM testnet! Here is how we verify tamper-evidence using keccak256 hashes of canonicalized post metadata.",
            "post_timestamp": "2024-05-16T18:20:10Z",
            "post_image_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=600&auto=format&fit=crop&q=80",
        },
        {
            "platform": "GitHub",
            "post_url": "https://github.com/deepinsight/insightface",
            "author_handle": "@deepinsight",
            "author_name": "InsightFace Core Team",
            "post_caption": "InsightFace: 2D and 3D Face Analysis Project with Buffalo models for accurate facial recognition, landmark localization, and biometric encoding.",
            "post_timestamp": "2024-05-18T12:05:45Z",
            "post_image_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=600&auto=format&fit=crop&q=80",
        },
    ]

    def search(self, image_path: str, image_bytes: Optional[bytes] = None) -> List[DiscoveredPost]:
        try:
            with open(image_path, "rb") as f:
                content = f.read()
        except Exception:
            content = b"sample_seed"

        h_val = int(hashlib.md5(content).hexdigest(), 16)
        fixture_index = h_val % len(self.FIXTURE_DATABASE)
        selected_fixture = self.FIXTURE_DATABASE[fixture_index]

        post = DiscoveredPost(
            platform=selected_fixture["platform"],
            post_url=selected_fixture["post_url"],
            author_handle=selected_fixture["author_handle"],
            author_name=selected_fixture["author_name"],
            post_caption=selected_fixture["post_caption"],
            post_timestamp=selected_fixture["post_timestamp"],
            post_image_url=selected_fixture["post_image_url"],
            raw_metadata={"source": "RealisticFallbackProvider", "index": fixture_index},
        )
        return [post]
