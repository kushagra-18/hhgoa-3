import json
import logging
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import desc, text

from src.database.models import (
    FaceScan,
    SearchMatch,
    BlockchainAttestation,
    VerificationAudit,
    HAS_PGVECTOR,
)

logger = logging.getLogger("repository")


class PipelineRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_face_scan(
        self,
        original_image_path: str,
        crop_image_path: str,
        image_sha256: str,
        embedding: np.ndarray,
        bbox: List[int],
        landmarks: List[List[int]],
        face_confidence: float = 1.0,
    ) -> FaceScan:
        """Create and persist a new face scan record."""
        embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
        
        scan = FaceScan(
            original_image_path=original_image_path,
            crop_image_path=crop_image_path,
            image_sha256=image_sha256,
            embedding=embedding_list,
            embedding_json=json.dumps(embedding_list),
            bbox_json=json.dumps(bbox),
            landmarks_json=json.dumps(landmarks),
            face_confidence=face_confidence,
        )
        self.db.add(scan)
        self.db.commit()
        self.db.refresh(scan)
        return scan

    def get_face_scan(self, scan_id: int) -> Optional[FaceScan]:
        return self.db.query(FaceScan).filter(FaceScan.id == scan_id).first()

    def get_face_scan_by_uuid(self, scan_uuid: str) -> Optional[FaceScan]:
        return self.db.query(FaceScan).filter(FaceScan.scan_uuid == scan_uuid).first()

    def search_similar_faces(
        self, target_embedding: np.ndarray, top_k: int = 5
    ) -> List[Tuple[FaceScan, float]]:
        """
        Search for top-K nearest face vectors using pgvector cosine distance if in PostgreSQL,
        or vectorized NumPy cosine similarity in SQLite.
        """
        target_list = target_embedding.tolist() if isinstance(target_embedding, np.ndarray) else target_embedding
        target_arr = np.array(target_list, dtype=np.float32)
        norm_target = np.linalg.norm(target_arr)
        if norm_target > 0:
            target_arr = target_arr / norm_target

        # Try pgvector query first if available
        try:
            if HAS_PGVECTOR and hasattr(FaceScan, "embedding") and self.db.bind.dialect.name == "postgresql":
                # pgvector cosine distance operator is <=>
                results = (
                    self.db.query(
                        FaceScan,
                        (1 - FaceScan.embedding.cosine_distance(target_list)).label("similarity"),
                    )
                    .order_by(FaceScan.embedding.cosine_distance(target_list))
                    .limit(top_k)
                    .all()
                )
                return [(row[0], float(row[1])) for row in results]
        except Exception as e:
            logger.debug(f"pgvector native search skipped ({e}), falling back to memory cosine.")

        # In-memory cosine distance fallback
        all_scans = self.db.query(FaceScan).all()
        scored = []
        for s in all_scans:
            if not s.embedding_json:
                continue
            emb = np.array(json.loads(s.embedding_json), dtype=np.float32)
            norm_emb = np.linalg.norm(emb)
            if norm_emb > 0:
                emb = emb / norm_emb
            similarity = float(np.dot(target_arr, emb))
            scored.append((s, similarity))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def create_search_match(
        self,
        scan_id: int,
        platform: str,
        post_url: str,
        author_handle: str,
        author_name: str,
        post_caption: str,
        post_timestamp: str,
        post_image_url: str,
        post_image_sha256: str,
        visual_similarity_score: float,
        raw_metadata: Dict[str, Any],
    ) -> SearchMatch:
        """Record a social media search match."""
        match = SearchMatch(
            scan_id=scan_id,
            platform=platform,
            post_url=post_url,
            author_handle=author_handle,
            author_name=author_name,
            post_caption=post_caption,
            post_timestamp=post_timestamp,
            post_image_url=post_image_url,
            post_image_sha256=post_image_sha256,
            visual_similarity_score=visual_similarity_score,
            raw_metadata=json.dumps(raw_metadata),
        )
        self.db.add(match)
        self.db.commit()
        self.db.refresh(match)
        return match

    def get_search_match(self, match_id: int) -> Optional[SearchMatch]:
        return self.db.query(SearchMatch).filter(SearchMatch.id == match_id).first()

    def create_blockchain_attestation(
        self,
        scan_id: int,
        search_match_id: int,
        payload_hash: str,
        face_hash: str,
        tx_hash: str,
        block_number: int,
        contract_address: str,
        network_name: str,
        submitter_address: str,
        metadata_uri: str,
        raw_receipt: Dict[str, Any],
        is_verified: bool = True,
    ) -> BlockchainAttestation:
        """Record an on-chain attestation receipt."""
        attestation = BlockchainAttestation(
            scan_id=scan_id,
            search_match_id=search_match_id,
            payload_hash=payload_hash,
            face_hash=face_hash,
            tx_hash=tx_hash,
            block_number=block_number,
            contract_address=contract_address,
            network_name=network_name,
            submitter_address=submitter_address,
            metadata_uri=metadata_uri,
            raw_receipt_json=json.dumps(raw_receipt),
            is_verified=is_verified,
        )
        self.db.add(attestation)
        self.db.commit()
        self.db.refresh(attestation)
        return attestation

    def get_attestation(self, attestation_id: int) -> Optional[BlockchainAttestation]:
        return self.db.query(BlockchainAttestation).filter(BlockchainAttestation.id == attestation_id).first()

    def get_attestation_by_hash(self, payload_hash: str) -> Optional[BlockchainAttestation]:
        return self.db.query(BlockchainAttestation).filter(BlockchainAttestation.payload_hash == payload_hash).first()

    def create_verification_audit(
        self,
        attestation_id: int,
        is_valid: bool,
        calculated_payload_hash: str,
        onchain_payload_hash: str,
        calculated_face_hash: str,
        onchain_face_hash: str,
        tamper_details: Optional[Dict[str, Any]] = None,
    ) -> VerificationAudit:
        """Persist a verification audit log."""
        audit = VerificationAudit(
            attestation_id=attestation_id,
            is_valid=is_valid,
            calculated_payload_hash=calculated_payload_hash,
            onchain_payload_hash=onchain_payload_hash,
            calculated_face_hash=calculated_face_hash,
            onchain_face_hash=onchain_face_hash,
            tamper_details=json.dumps(tamper_details) if tamper_details else None,
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        return audit

    def list_all_pipeline_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all pipeline runs with their full join metadata."""
        attestations = (
            self.db.query(BlockchainAttestation)
            .order_by(desc(BlockchainAttestation.created_at))
            .limit(limit)
            .all()
        )
        runs = []
        for a in attestations:
            scan = a.face_scan
            match = a.search_match
            latest_audit = self.db.query(VerificationAudit).filter(VerificationAudit.attestation_id == a.id).order_by(desc(VerificationAudit.audited_at)).first()
            runs.append({
                "attestation": a.to_dict(),
                "face_scan": scan.to_dict() if scan else None,
                "search_match": match.to_dict() if match else None,
                "latest_audit": latest_audit.to_dict() if latest_audit else None,
            })
        return runs
