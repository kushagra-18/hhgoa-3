import copy
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List

from src.blockchain.anchor import BlockchainAnchor
from src.search.social_parser import DiscoveredPost
from src.face.detector import FaceDetectionResult

logger = logging.getLogger("blockchain_verifier")


@dataclass
class VerificationResult:
    """Comprehensive result of verifying local face & social data against on-chain anchor."""
    is_valid: bool
    onchain_record_found: bool
    calculated_payload_hash: str
    onchain_payload_hash: str
    calculated_face_hash: str
    onchain_face_hash: str
    block_timestamp: Optional[int] = None
    submitter_address: Optional[str] = None
    metadata_uri: Optional[str] = None
    tampered_fields: List[Dict[str, Any]] = field(default_factory=list)
    verification_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BlockchainVerifier:
    """
    Validates integrity of social media discoveries and facial scan embeddings
    against immutable on-chain smart contract attestations.
    """

    def __init__(self, anchor: Optional[BlockchainAnchor] = None):
        self.anchor = anchor or BlockchainAnchor()

    def verify(
        self,
        post: DiscoveredPost,
        face_result: FaceDetectionResult,
        target_payload_hash: Optional[str] = None,
    ) -> VerificationResult:
        """
        Recomputes local Keccak256 hashes and compares with on-chain record.
        """
        calc_payload_hash = self.anchor.compute_payload_hash(post)
        calc_face_hash = self.anchor.compute_face_hash(face_result)

        lookup_hash = target_payload_hash or calc_payload_hash
        onchain_record = self.anchor.get_onchain_record(lookup_hash)

        if not onchain_record:
            return VerificationResult(
                is_valid=False,
                onchain_record_found=False,
                calculated_payload_hash=calc_payload_hash,
                onchain_payload_hash="0x0000000000000000000000000000000000000000000000000000000000000000",
                calculated_face_hash=calc_face_hash,
                onchain_face_hash="0x0000000000000000000000000000000000000000000000000000000000000000",
                verification_summary="Verification FAILED: No matching attestation found on-chain for given payload hash.",
            )

        onchain_p_hash = onchain_record.get("payload_hash", "")
        onchain_f_hash = onchain_record.get("face_hash", "")
        timestamp = onchain_record.get("block_timestamp")
        submitter = onchain_record.get("submitter")
        uri = onchain_record.get("metadata_uri")

        payload_match = calc_payload_hash.lower() == onchain_p_hash.lower()
        face_match = calc_face_hash.lower() == onchain_f_hash.lower()

        tampered_fields = []
        if not payload_match:
            # Detect which field was tampered by checking original canonical post if present
            orig_post = onchain_record.get("post_canonical", {})
            current_dict = post.canonical_dict()
            for k, cur_val in current_dict.items():
                orig_val = orig_post.get(k)
                if orig_val is not None and cur_val != orig_val:
                    tampered_fields.append({
                        "field": k,
                        "expected_original": orig_val,
                        "tampered_current": cur_val,
                    })

            if not tampered_fields:
                tampered_fields.append({
                    "field": "payload_content",
                    "expected_original": onchain_p_hash,
                    "tampered_current": calc_payload_hash,
                })

        if not face_match:
            tampered_fields.append({
                "field": "facial_embedding_or_image",
                "expected_original": onchain_f_hash,
                "tampered_current": calc_face_hash,
            })

        is_valid = payload_match and face_match

        if is_valid:
            summary = (
                f"✅ Cryptographic Verification SUCCESSFUL!\n"
                f"• Block Timestamp: {timestamp}\n"
                f"• Submitter Address: {submitter}\n"
                f"• On-Chain Payload Hash: {onchain_p_hash}\n"
                f"• On-Chain Face Hash: {onchain_f_hash}\n"
                f"• Integrity: 100% Verified Untampered."
            )
        else:
            summary = (
                f"❌ Cryptographic Verification FAILED! Tampering Detected.\n"
                f"• Calculated Hash: {calc_payload_hash}\n"
                f"• On-Chain Hash: {onchain_p_hash}\n"
                f"• Tampered Fields Count: {len(tampered_fields)}"
            )

        return VerificationResult(
            is_valid=is_valid,
            onchain_record_found=True,
            calculated_payload_hash=calc_payload_hash,
            onchain_payload_hash=onchain_p_hash,
            calculated_face_hash=calc_face_hash,
            onchain_face_hash=onchain_f_hash,
            block_timestamp=timestamp,
            submitter_address=submitter,
            metadata_uri=uri,
            tampered_fields=tampered_fields,
            verification_summary=summary,
        )

    def run_tamper_demonstration(
        self,
        post: DiscoveredPost,
        face_result: FaceDetectionResult,
        original_payload_hash: str,
    ) -> Dict[str, Any]:
        """
        Runs a side-by-side comparison:
        1. Verifying authentic data -> PASS
        2. Modifying caption and author -> FAIL with detected diffs
        """
        # 1. Verify genuine data
        genuine_res = self.verify(post, face_result, original_payload_hash)

        # 2. Create tampered post clone
        tampered_post = copy.deepcopy(post)
        tampered_post.post_caption = "🚨 [TAMPERED] This caption was maliciously modified after blockchain anchoring."
        tampered_post.author_name = "Malicious Impersonator"
        
        tampered_res = self.verify(tampered_post, face_result, original_payload_hash)

        return {
            "original_hash": original_payload_hash,
            "genuine_verification": genuine_res.to_dict(),
            "tampered_verification": tampered_res.to_dict(),
        }
