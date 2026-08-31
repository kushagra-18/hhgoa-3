import json
import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base, FaceScan, SearchMatch, BlockchainAttestation
from src.database.repository import PipelineRepository


@pytest.fixture
def db_session():
    # Use in-memory SQLite database for isolated test execution
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_repository_crud(db_session):
    repo = PipelineRepository(db_session)

    # 1. Create Face Scan
    emb = np.random.randn(512).astype(np.float32)
    scan = repo.create_face_scan(
        original_image_path="test.jpg",
        crop_image_path="crop.jpg",
        image_sha256="abc123sha",
        embedding=emb,
        bbox=[50, 50, 200, 200],
        landmarks=[[10, 10], [20, 20]],
    )
    assert scan.id is not None
    assert scan.image_sha256 == "abc123sha"

    # 2. Create Search Match
    match = repo.create_search_match(
        scan_id=scan.id,
        platform="Twitter/X",
        post_url="https://x.com/post/1",
        author_handle="@tester",
        author_name="Tester",
        post_caption="Sample post",
        post_timestamp="2024-05-11",
        post_image_url="https://img.com/1",
        post_image_sha256="imgsha123",
        visual_similarity_score=0.96,
        raw_metadata={"key": "val"},
    )
    assert match.id is not None
    assert match.scan_id == scan.id

    # 3. Create Blockchain Attestation
    attestation = repo.create_blockchain_attestation(
        scan_id=scan.id,
        search_match_id=match.id,
        payload_hash="0x1111111111111111111111111111111111111111111111111111111111111111",
        face_hash="0x2222222222222222222222222222222222222222222222222222222222222222",
        tx_hash="0x3333333333333333333333333333333333333333333333333333333333333333",
        block_number=100,
        contract_address="0x4444444444444444444444444444444444444444",
        network_name="Local-EVM",
        submitter_address="0x5555555555555555555555555555555555555555",
        metadata_uri="ipfs://test",
        raw_receipt={},
    )
    assert attestation.id is not None

    # 4. List runs
    runs = repo.list_all_pipeline_runs()
    assert len(runs) == 1
    assert runs[0]["attestation"]["payload_hash"] == "0x1111111111111111111111111111111111111111111111111111111111111111"


def test_vector_similarity_search(db_session):
    repo = PipelineRepository(db_session)

    # Insert 3 scans with distinct embeddings
    v1 = np.ones(512, dtype=np.float32)
    v2 = np.zeros(512, dtype=np.float32)
    v2[0] = 1.0
    v3 = np.full(512, -1.0, dtype=np.float32)

    s1 = repo.create_face_scan("s1.jpg", "", "sha1", v1, [0,0,10,10], [])
    s2 = repo.create_face_scan("s2.jpg", "", "sha2", v2, [0,0,10,10], [])
    s3 = repo.create_face_scan("s3.jpg", "", "sha3", v3, [0,0,10,10], [])

    # Search query closely aligned with v1
    query_v = np.ones(512, dtype=np.float32) * 0.99
    results = repo.search_similar_faces(query_v, top_k=2)

    assert len(results) == 2
    # Top match should be s1
    assert results[0][0].id == s1.id
    assert results[0][1] > 0.98
