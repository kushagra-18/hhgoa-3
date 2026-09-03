import time
import json
import logging
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any, Union, Iterator, Callable
import queue
import threading
import numpy as np

from src.config import settings
from src.database.session import SessionLocal, init_db
from src.database.repository import PipelineRepository
from src.database.models import FaceScan, SearchMatch, BlockchainAttestation
from src.face.detector import FaceDetector, FaceDetectionResult
from src.search.engine import SearchEngine
from src.search.social_parser import DiscoveredPost
from src.blockchain.anchor import BlockchainAnchor, AttestationReceipt
from src.blockchain.verifier import BlockchainVerifier, VerificationResult

logger = logging.getLogger("pipeline")


@dataclass
class PipelineResult:
    """Complete end-to-end execution outcome."""
    success: bool
    face_scan: Optional[Dict[str, Any]] = None
    search_match: Optional[Dict[str, Any]] = None
    blockchain_attestation: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    elapsed_seconds: float = 0.0
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FaceVerificationPipeline:
    """
    Complete Pipeline Orchestrator:
    Face Scan Input -> Reverse Search / Social Discovery -> Blockchain Attestation -> Database & Verification
    """

    def __init__(
        self,
        face_detector: Optional[FaceDetector] = None,
        search_engine: Optional[SearchEngine] = None,
        blockchain_anchor: Optional[BlockchainAnchor] = None,
        blockchain_verifier: Optional[BlockchainVerifier] = None,
        similarity_threshold: Optional[float] = None,
    ):
        self.face_detector = face_detector or FaceDetector()
        self.search_engine = search_engine or SearchEngine(
            face_detector=self.face_detector,
            similarity_threshold=similarity_threshold,
        )
        self.anchor = blockchain_anchor or BlockchainAnchor()
        self.verifier = blockchain_verifier or BlockchainVerifier(anchor=self.anchor)

    def run(
        self,
        image_input: Union[str, Path, bytes, np.ndarray],
        save_db: bool = True,
        metadata_uri: Optional[str] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> PipelineResult:
        """
        Execute full end-to-end pipeline:
        1. Detect face & extract 512-dim embedding (InsightFace Buffalo)
        2. Reverse web & social media search for matching post
        3. Cryptographically hash & anchor to EVM Blockchain Smart Contract
        4. Persist to PostgreSQL with pgvector (or SQLite)
        5. Perform immediate on-chain tamper verification
        """
        start_time = time.time()
        logger.info("Starting Face Identification & Blockchain Verification Pipeline...")

        if progress_callback:
            progress_callback({
                "type": "progress",
                "step": 1,
                "total_steps": 5,
                "percent": 15,
                "title": "Finding Face",
                "message": "Detecting face and analyzing features...",
            })

        # Step 1: Face Detection & Encoding
        face_result = self.face_detector.detect_and_encode(image_input)
        if not face_result.detected:
            if progress_callback:
                progress_callback({
                    "type": "error",
                    "step": 1,
                    "percent": 100,
                    "title": "No Face Found",
                    "message": face_result.error_message or "No face detected in image. Please try another photo.",
                })
            return PipelineResult(
                success=False,
                elapsed_seconds=round(time.time() - start_time, 3),
                error_message=face_result.error_message or "No face detected in input image.",
            )

        if progress_callback:
            progress_callback({
                "type": "progress",
                "step": 2,
                "total_steps": 5,
                "percent": 30,
                "title": "Face Located",
                "message": "Face located. Searching public web for visual matches...",
            })

        # Step 2: Reverse Image / Social Media Search & Batch Scoring
        input_path_str = str(image_input) if isinstance(image_input, (str, Path)) else "memory_buffer"
        discovered_post = self.search_engine.search_for_matching_post(
            image_path=input_path_str,
            query_face_result=face_result,
            progress_callback=progress_callback,
        )

        if not discovered_post:
            if progress_callback:
                progress_callback({
                    "type": "error",
                    "step": 3,
                    "percent": 100,
                    "title": "No Match",
                    "message": "Failed to discover matching public photos.",
                })
            return PipelineResult(
                success=False,
                face_scan={
                    "bbox": face_result.bbox,
                    "confidence": face_result.confidence,
                    "crop_path": face_result.crop_path,
                },
                elapsed_seconds=round(time.time() - start_time, 3),
                error_message="Failed to discover matching social media post.",
            )

        # Step 3: Blockchain Attestation Anchor
        if progress_callback:
            progress_callback({
                "type": "progress",
                "step": 4,
                "total_steps": 5,
                "percent": 80,
                "title": "Recording Attestation",
                "message": "Recording attestation on blockchain...",
            })

        attestation_receipt = self.anchor.anchor_attestation(
            post=discovered_post,
            face_result=face_result,
            metadata_uri=metadata_uri,
        )

        # Step 4: Verification Check against On-Chain State
        if progress_callback:
            progress_callback({
                "type": "progress",
                "step": 5,
                "total_steps": 5,
                "percent": 92,
                "title": "Verifying Record",
                "message": "Checking cryptographic integrity against blockchain...",
            })

        verification_result = self.verifier.verify(
            post=discovered_post,
            face_result=face_result,
            target_payload_hash=attestation_receipt.payload_hash,
        )

        # Step 5: Database Persistence
        db_scan_dict, db_match_dict, db_attest_dict = None, None, None
        if save_db:
            try:
                with SessionLocal() as db:
                    repo = PipelineRepository(db)

                    # Save Face Scan
                    saved_scan = repo.create_face_scan(
                        original_image_path=input_path_str,
                        crop_image_path=face_result.crop_path or "",
                        image_sha256=face_result.image_sha256,
                        embedding=face_result.embedding if face_result.embedding is not None else np.zeros(512),
                        bbox=face_result.bbox,
                        landmarks=face_result.landmarks,
                        face_confidence=face_result.confidence,
                    )
                    db_scan_dict = saved_scan.to_dict()

                    # Save Search Match
                    saved_match = repo.create_search_match(
                        scan_id=saved_scan.id,
                        platform=discovered_post.platform,
                        post_url=discovered_post.post_url,
                        author_handle=discovered_post.author_handle,
                        author_name=discovered_post.author_name,
                        post_caption=discovered_post.post_caption,
                        post_timestamp=discovered_post.post_timestamp,
                        post_image_url=discovered_post.post_image_url,
                        post_image_sha256=discovered_post.post_image_sha256,
                        visual_similarity_score=discovered_post.visual_similarity_score,
                        raw_metadata=discovered_post.raw_metadata,
                    )
                    db_match_dict = saved_match.to_dict()

                    # Save Blockchain Attestation
                    saved_attestation = repo.create_blockchain_attestation(
                        scan_id=saved_scan.id,
                        search_match_id=saved_match.id,
                        payload_hash=attestation_receipt.payload_hash,
                        face_hash=attestation_receipt.face_hash,
                        tx_hash=attestation_receipt.tx_hash,
                        block_number=attestation_receipt.block_number,
                        contract_address=attestation_receipt.contract_address,
                        network_name=attestation_receipt.network_name,
                        submitter_address=attestation_receipt.submitter_address,
                        metadata_uri=attestation_receipt.metadata_uri,
                        raw_receipt=attestation_receipt.raw_receipt,
                        is_verified=verification_result.is_valid,
                    )
                    db_attest_dict = saved_attestation.to_dict()

                    # Save Verification Audit
                    repo.create_verification_audit(
                        attestation_id=saved_attestation.id,
                        is_valid=verification_result.is_valid,
                        calculated_payload_hash=verification_result.calculated_payload_hash,
                        onchain_payload_hash=verification_result.onchain_payload_hash,
                        calculated_face_hash=verification_result.calculated_face_hash,
                        onchain_face_hash=verification_result.onchain_face_hash,
                        tamper_details={"tampered_fields": verification_result.tampered_fields},
                    )

            except Exception as e:
                logger.error(f"Database persistence encountered error: {e}")

        elapsed = round(time.time() - start_time, 3)
        logger.info(f"Pipeline finished successfully in {elapsed}s.")

        final_res = PipelineResult(
            success=True,
            face_scan=db_scan_dict or {
                "bbox": face_result.bbox,
                "confidence": face_result.confidence,
                "crop_path": face_result.crop_path,
                "overlay_path": face_result.overlay_path,
                "image_sha256": face_result.image_sha256,
                "crop_sha256": face_result.crop_sha256,
            },
            search_match=db_match_dict or discovered_post.to_dict(),
            blockchain_attestation=db_attest_dict or attestation_receipt.to_dict(),
            verification=verification_result.to_dict(),
            elapsed_seconds=elapsed,
        )

        if progress_callback:
            progress_callback({
                "type": "complete",
                "step": 5,
                "percent": 100,
                "title": "Complete",
                "message": "Verification complete!",
                "result": final_res.to_dict(),
            })

        return final_res

    def run_stream(
        self,
        image_input: Union[str, Path, bytes, np.ndarray],
        save_db: bool = True,
        metadata_uri: Optional[str] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Stream real-time progress events and the final verification outcome via generator.
        """
        event_queue: queue.Queue = queue.Queue()

        def _worker():
            try:
                self.run(
                    image_input=image_input,
                    save_db=save_db,
                    metadata_uri=metadata_uri,
                    progress_callback=event_queue.put,
                )
            except Exception as e:
                logger.exception("Error during streaming pipeline run")
                event_queue.put({
                    "type": "error",
                    "step": 1,
                    "percent": 100,
                    "title": "Error",
                    "message": str(e),
                })
            finally:
                event_queue.put(None)

        worker_thread = threading.Thread(target=_worker, daemon=True)
        worker_thread.start()

        while True:
            try:
                ev = event_queue.get(timeout=0.1)
                if ev is None:
                    break
                yield ev
                if ev.get("type") in ("complete", "error"):
                    break
            except queue.Empty:
                if not worker_thread.is_alive() and event_queue.empty():
                    break

    def test_tampering_for_attestation(self, attestation_id: int) -> Dict[str, Any]:
        """Runs a live tamper simulation on a recorded attestation."""
        with SessionLocal() as db:
            repo = PipelineRepository(db)
            attestation = repo.get_attestation(attestation_id)
            if not attestation:
                return {"error": f"Attestation #{attestation_id} not found."}

            scan = attestation.face_scan
            match = attestation.search_match
            if not scan or not match:
                return {"error": "Associated scan or match record missing."}

            # Reconstruct objects
            post = DiscoveredPost(
                platform=match.platform,
                post_url=match.post_url,
                author_handle=match.author_handle or "",
                author_name=match.author_name or "",
                post_caption=match.post_caption or "",
                post_timestamp=match.post_timestamp or "",
                post_image_url=match.post_image_url or "",
                post_image_sha256=match.post_image_sha256 or "",
                visual_similarity_score=match.visual_similarity_score or 0.0,
            )

            emb = np.array(json.loads(scan.embedding_json), dtype=np.float32) if scan.embedding_json else np.zeros(512)
            face_res = FaceDetectionResult(
                detected=True,
                image_sha256=scan.image_sha256,
                crop_sha256="",
                embedding=emb,
            )

            return self.verifier.run_tamper_demonstration(
                post=post,
                face_result=face_res,
                original_payload_hash=attestation.payload_hash,
            )
