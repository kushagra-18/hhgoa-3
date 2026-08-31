import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    JSON,
)
from sqlalchemy.orm import declarative_base, relationship

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False
    Vector = None

Base = declarative_base()


class FaceScan(Base):
    """Stores the original face scan, bounding boxes, landmarks, and 512-dim embedding."""
    __tablename__ = "face_scans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    original_image_path = Column(String(512), nullable=False)
    crop_image_path = Column(String(512), nullable=True)
    image_sha256 = Column(String(64), nullable=False, index=True)
    
    # 512-dimensional vector embedding
    if HAS_PGVECTOR:
        embedding = Column(Vector(512), nullable=True)
    else:
        embedding = Column(JSON, nullable=True)
        
    embedding_json = Column(Text, nullable=True) # Full JSON representation for cross-compatibility
    bbox_json = Column(Text, nullable=True)
    landmarks_json = Column(Text, nullable=True)
    face_confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    search_matches = relationship("SearchMatch", back_populates="face_scan", cascade="all, delete-orphan")
    attestations = relationship("BlockchainAttestation", back_populates="face_scan", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "scan_uuid": self.scan_uuid,
            "original_image_path": self.original_image_path,
            "crop_image_path": self.crop_image_path,
            "image_sha256": self.image_sha256,
            "bbox": json.loads(self.bbox_json) if self.bbox_json else [],
            "landmarks": json.loads(self.landmarks_json) if self.landmarks_json else [],
            "face_confidence": self.face_confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SearchMatch(Base):
    """Stores discovered web and social media posts matching the scanned face."""
    __tablename__ = "search_matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, ForeignKey("face_scans.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(64), nullable=False) # Twitter, LinkedIn, Instagram, Reddit, Web
    post_url = Column(String(1024), nullable=False)
    author_handle = Column(String(256), nullable=True)
    author_name = Column(String(256), nullable=True)
    post_caption = Column(Text, nullable=True)
    post_timestamp = Column(String(128), nullable=True)
    post_image_url = Column(String(1024), nullable=True)
    post_image_sha256 = Column(String(64), nullable=True)
    visual_similarity_score = Column(Float, default=0.0)
    raw_metadata = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    face_scan = relationship("FaceScan", back_populates="search_matches")
    attestations = relationship("BlockchainAttestation", back_populates="search_match", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "platform": self.platform,
            "post_url": self.post_url,
            "author_handle": self.author_handle,
            "author_name": self.author_name,
            "post_caption": self.post_caption,
            "post_timestamp": self.post_timestamp,
            "post_image_url": self.post_image_url,
            "post_image_sha256": self.post_image_sha256,
            "visual_similarity_score": self.visual_similarity_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BlockchainAttestation(Base):
    """Stores immutable on-chain record references, cryptographic hashes, and tx receipts."""
    __tablename__ = "blockchain_attestations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, ForeignKey("face_scans.id", ondelete="CASCADE"), nullable=False, index=True)
    search_match_id = Column(Integer, ForeignKey("search_matches.id", ondelete="CASCADE"), nullable=False, index=True)
    
    payload_hash = Column(String(66), nullable=False, index=True) # 0x + 64 hex chars (keccak256)
    face_hash = Column(String(66), nullable=False, index=True)
    tx_hash = Column(String(66), nullable=False, index=True)
    block_number = Column(Integer, nullable=False)
    contract_address = Column(String(42), nullable=False)
    network_name = Column(String(64), nullable=False)
    submitter_address = Column(String(42), nullable=False)
    metadata_uri = Column(String(512), nullable=True)
    raw_receipt_json = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    face_scan = relationship("FaceScan", back_populates="attestations")
    search_match = relationship("SearchMatch", back_populates="attestations")
    audits = relationship("VerificationAudit", back_populates="attestation", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "search_match_id": self.search_match_id,
            "payload_hash": self.payload_hash,
            "face_hash": self.face_hash,
            "tx_hash": self.tx_hash,
            "block_number": self.block_number,
            "contract_address": self.contract_address,
            "network_name": self.network_name,
            "submitter_address": self.submitter_address,
            "metadata_uri": self.metadata_uri,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class VerificationAudit(Base):
    """Stores records of verification attempts, comparing on-chain state vs computed local hashes."""
    __tablename__ = "verification_audits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    attestation_id = Column(Integer, ForeignKey("blockchain_attestations.id", ondelete="CASCADE"), nullable=False, index=True)
    is_valid = Column(Boolean, nullable=False)
    calculated_payload_hash = Column(String(66), nullable=False)
    onchain_payload_hash = Column(String(66), nullable=False)
    calculated_face_hash = Column(String(66), nullable=False)
    onchain_face_hash = Column(String(66), nullable=False)
    tamper_details = Column(Text, nullable=True)
    audited_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    attestation = relationship("BlockchainAttestation", back_populates="audits")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "attestation_id": self.attestation_id,
            "is_valid": self.is_valid,
            "calculated_payload_hash": self.calculated_payload_hash,
            "onchain_payload_hash": self.onchain_payload_hash,
            "calculated_face_hash": self.calculated_face_hash,
            "onchain_face_hash": self.onchain_face_hash,
            "tamper_details": json.loads(self.tamper_details) if self.tamper_details else None,
            "audited_at": self.audited_at.isoformat() if self.audited_at else None,
        }
