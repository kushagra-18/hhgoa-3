import numpy as np
import pytest
from src.blockchain.anchor import BlockchainAnchor, AttestationReceipt
from src.blockchain.verifier import BlockchainVerifier, VerificationResult
from src.search.social_parser import DiscoveredPost
from src.face.detector import FaceDetectionResult


@pytest.fixture
def sample_data():
    post = DiscoveredPost(
        platform="Twitter/X",
        post_url="https://x.com/sataboris/status/1789234901840192831",
        author_handle="@sataboris",
        author_name="Satoshi Borisov",
        post_caption="Excited to share our research on on-chain face attestation!",
        post_timestamp="2024-05-11T16:42:00Z",
        post_image_url="https://images.unsplash.com/photo-1534528741775",
        post_image_sha256="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
    )

    face_res = FaceDetectionResult(
        detected=True,
        bbox=[100, 100, 300, 300],
        embedding=np.random.randn(512).astype(np.float32),
        image_sha256="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
        crop_sha256="4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
    )
    return post, face_res


def test_blockchain_anchor_and_verify(sample_data):
    post, face_res = sample_data
    anchor = BlockchainAnchor()
    verifier = BlockchainVerifier(anchor=anchor)

    # 1. Compute hashes
    payload_hash = anchor.compute_payload_hash(post)
    face_hash = anchor.compute_face_hash(face_res)
    assert payload_hash.startswith("0x") and len(payload_hash) == 66
    assert face_hash.startswith("0x") and len(face_hash) == 66

    # 2. Anchor attestation
    receipt = anchor.anchor_attestation(post, face_res)
    assert isinstance(receipt, AttestationReceipt)
    assert receipt.payload_hash == payload_hash
    assert receipt.block_number > 0
    assert receipt.tx_hash.startswith("0x")

    # 3. Verify on-chain record with original data
    ver_res = verifier.verify(post, face_res, receipt.payload_hash)
    assert isinstance(ver_res, VerificationResult)
    assert ver_res.is_valid is True
    assert ver_res.onchain_record_found is True
    assert len(ver_res.tampered_fields) == 0


def test_tamper_detection(sample_data):
    post, face_res = sample_data
    anchor = BlockchainAnchor()
    verifier = BlockchainVerifier(anchor=anchor)

    # Anchor genuine data
    receipt = anchor.anchor_attestation(post, face_res)

    # Run tamper demonstration
    demo = verifier.run_tamper_demonstration(post, face_res, receipt.payload_hash)
    assert demo["genuine_verification"]["is_valid"] is True
    assert demo["tampered_verification"]["is_valid"] is False
    assert len(demo["tampered_verification"]["tampered_fields"]) > 0
