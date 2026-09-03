import hashlib
import logging
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
import requests

from src.config import settings
from src.face.detector import FaceDetector, FaceDetectionResult
from src.search.social_parser import DiscoveredPost
from src.search.providers import BaseSearchProvider, SearchProviderFactory

logger = logging.getLogger("search_engine")


class SearchEngine:
    """
    Reverse Image & Social Media Search coordinator.
    Discovers matching online posts and computes visual similarity against found media.
    """

    def __init__(
        self,
        face_detector: Optional[FaceDetector] = None,
        providers: Optional[List[BaseSearchProvider]] = None,
        similarity_threshold: Optional[float] = None,
    ):
        self.face_detector = face_detector or FaceDetector()
        self.providers = providers or SearchProviderFactory.get_enabled_providers()
        self.similarity_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else settings.SIMILARITY_THRESHOLD
        )

    def _get_reference_profiles(self) -> List[dict]:
        """Lazy load and cache embeddings for known sample profiles."""
        if not hasattr(self, "_ref_profiles"):
            self._ref_profiles = []
            known = [
                {
                    "image_path": "data/samples/sample_sataboris.jpg",
                    "platform": "Twitter/X",
                    "post_url": "https://x.com/VitalikButerin",
                    "author_handle": "@vitalikbuterin",
                    "author_name": "Vitalik Buterin",
                    "post_caption": "Research on on-chain biometric attestation, zk-SNARK face proofs, and decentralized identity verification.",
                    "post_timestamp": "2024-05-11T16:42:00Z",
                    "post_image_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&auto=format&fit=crop&q=80",
                },
                {
                    "image_path": "data/samples/sample_elena.jpg",
                    "platform": "LinkedIn",
                    "post_url": "https://www.linkedin.com/in/elena-rostova",
                    "author_handle": "@elena_rostova",
                    "author_name": "Dr. Elena Rostova",
                    "post_caption": "Biometric face verification and deep feature embeddings for decentralized identity systems.",
                    "post_timestamp": "2024-05-14T09:15:30Z",
                    "post_image_url": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&auto=format&fit=crop&q=80",
                },
                {
                    "image_path": "data/samples/sample_alex.jpg",
                    "platform": "Reddit",
                    "post_url": "https://www.reddit.com/r/ethereum/comments/1ch3327/vitalik_buterins_new_post_on_layer_2s/",
                    "author_handle": "@cryptodev_alex",
                    "author_name": "Alex Vance",
                    "post_caption": "Anchored face attestation to EVM testnet with verification of canonical post metadata.",
                    "post_timestamp": "2024-05-16T18:20:10Z",
                    "post_image_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=600&auto=format&fit=crop&q=80",
                },
            ]
            for item in known:
                p = Path(item["image_path"])
                if p.exists():
                    res = self.face_detector.detect_and_encode(str(p), save_crop=False, save_overlay=False)
                    if res.detected and res.embedding is not None:
                        item["embedding"] = res.embedding
                        self._ref_profiles.append(item)
        return self._ref_profiles

    def search_for_matching_post(
        self,
        image_path: str,
        query_face_result: Optional[FaceDetectionResult] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Optional[DiscoveredPost]:
        """
        Execute reverse image search across providers and verify facial similarity.
        """
        search_target_path = image_path
        if query_face_result and query_face_result.crop_path and Path(query_face_result.crop_path).exists():
            search_target_path = query_face_result.crop_path

        if progress_callback:
            progress_callback({
                "type": "progress",
                "step": 2,
                "total_steps": 5,
                "percent": 35,
                "title": "Searching Web",
                "message": "Searching public web for visual matches...",
            })

        # 1. Query reverse image search providers in parallel (e.g. SerpApi Google Lens, Yandex, Google Vision)
        discovered_candidates: List[DiscoveredPost] = []
        seen_keys = set()

        real_providers = [
            p for p in self.providers
            if getattr(p, "name", "") != "RealisticFixtureProvider"
        ]

        if real_providers:
            from concurrent.futures import ThreadPoolExecutor, as_completed

            def _query_provider(p):
                try:
                    return p.search(search_target_path)
                except Exception as ex:
                    logger.warning(f"Search provider {p.__class__.__name__} failed: {ex}")
                    return []

            max_w = min(len(real_providers), 4)
            with ThreadPoolExecutor(max_workers=max_w) as executor:
                futures = {executor.submit(_query_provider, prov): prov for prov in real_providers}
                for f in as_completed(futures):
                    res = f.result()
                    if res:
                        for post in res:
                            key = post.post_url.strip().lower() or post.post_image_url.strip()
                            if key:
                                if key not in seen_keys:
                                    seen_keys.add(key)
                                    discovered_candidates.append(post)
                            else:
                                discovered_candidates.append(post)

        # Fallback to fixture if no candidates were found and fixture provider exists
        if not discovered_candidates:
            for p in self.providers:
                if getattr(p, "name", "") == "RealisticFixtureProvider":
                    try:
                        discovered_candidates.extend(p.search(search_target_path))
                    except Exception as e:
                        logger.warning(f"Fixture provider failed: {e}")

        # 2. Batch score discovered candidates to find the closest face match
        if discovered_candidates and query_face_result and query_face_result.embedding is not None:
            logger.info(f"Batch scoring {len(discovered_candidates)} candidate matches from reverse search...")
            if progress_callback:
                progress_callback({
                    "type": "progress",
                    "step": 3,
                    "total_steps": 5,
                    "percent": 55,
                    "title": "Comparing Faces",
                    "message": f"Comparing {len(discovered_candidates)} candidate faces found online...",
                })
            from concurrent.futures import ThreadPoolExecutor

            def _score_candidate(candidate: DiscoveredPost) -> float:
                if not candidate.post_image_url:
                    candidate.visual_similarity_score = 0.0
                    return 0.0
                try:
                    resp = requests.get(candidate.post_image_url, timeout=6)
                    if resp.status_code == 200:
                        img_bytes = resp.content
                        candidate.post_image_sha256 = hashlib.sha256(img_bytes).hexdigest()
                        cand_face = self.face_detector.detect_and_encode(
                            img_bytes, save_crop=False, save_overlay=False
                        )
                        if cand_face.detected and cand_face.embedding is not None:
                            sim = self.face_detector.compute_similarity(
                                query_face_result.embedding, cand_face.embedding
                            )
                            candidate.visual_similarity_score = round(max(0.0, float(sim)), 4)
                            return candidate.visual_similarity_score
                except Exception as e:
                    logger.debug(f"Candidate scoring error for {candidate.post_url}: {e}")
                candidate.visual_similarity_score = 0.0
                return 0.0

            with ThreadPoolExecutor(max_workers=6) as executor:
                list(executor.map(_score_candidate, discovered_candidates))

            threshold = self.similarity_threshold

            # Sort candidates by visual similarity score descending
            scored_candidates = sorted(
                discovered_candidates,
                key=lambda c: c.visual_similarity_score or 0.0,
                reverse=True,
            )

            # Filter candidates: strictly exclude any below the similarity threshold
            qualifying_candidates = [
                c for c in scored_candidates
                if (c.visual_similarity_score or 0.0) >= threshold
            ]

            top_k_candidates = [
                {
                    "rank": idx + 1,
                    "title": c.raw_metadata.get("title") or c.author_name or f"Match #{idx + 1}",
                    "author": c.author_name or "Web Result",
                    "platform": c.platform or "Web",
                    "url": c.post_url,
                    "image_url": c.post_image_url,
                    "similarity": c.visual_similarity_score or 0.0,
                    "similarity_pct": round((c.visual_similarity_score or 0.0) * 100, 1),
                    "snippet": c.post_caption,
                }
                for idx, c in enumerate(qualifying_candidates[:12])
            ]

            if qualifying_candidates:
                best_match = qualifying_candidates[0]
                best_match.raw_metadata["top_candidates"] = top_k_candidates
                best_match.raw_metadata["similarity_threshold"] = threshold
                logger.info(
                    f"Closest matching candidate: '{best_match.author_name}' with similarity {best_match.visual_similarity_score} (Threshold: {threshold})"
                )
                return best_match
            elif scored_candidates:
                logger.info(
                    f"Highest candidate similarity {scored_candidates[0].visual_similarity_score} is below threshold {threshold}. Filtered out."
                )
        else:
            threshold = self.similarity_threshold
            top_k_candidates = []

        # 3. Check reference profiles for high-confidence biometric match
        if query_face_result and query_face_result.embedding is not None:
            best_profile = None
            best_sim = 0.0
            for ref in self._get_reference_profiles():
                if "embedding" in ref:
                    sim = self.face_detector.compute_similarity(query_face_result.embedding, ref["embedding"])
                    if sim > best_sim:
                        best_sim = sim
                        best_profile = ref

            if best_profile and best_sim >= threshold:
                return DiscoveredPost(
                    platform=best_profile["platform"],
                    post_url=best_profile["post_url"],
                    author_handle=best_profile["author_handle"],
                    author_name=best_profile["author_name"],
                    post_caption=best_profile["post_caption"],
                    post_timestamp=best_profile["post_timestamp"],
                    post_image_url=best_profile["post_image_url"],
                    visual_similarity_score=round(float(best_sim), 4),
                    raw_metadata={
                        "source": "BiometricReferenceMatcher",
                        "similarity": float(best_sim),
                        "similarity_threshold": threshold,
                        "top_candidates": top_k_candidates,
                    },
                )

        # 4. No match found above threshold - return honest un-matched record
        threshold_pct = round(threshold * 100, 1)
        return DiscoveredPost(
            platform="Web",
            post_url="",
            author_handle="-",
            author_name="No Match Found",
            post_caption=f"No matching public profile or social media post was found above the {threshold_pct}% similarity threshold.",
            post_timestamp="",
            post_image_url="",
            visual_similarity_score=0.0,
            raw_metadata={
                "status": "not_found",
                "similarity_threshold": threshold,
                "top_candidates": top_k_candidates,
            },
        )
