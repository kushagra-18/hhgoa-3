import os
from pathlib import Path
import numpy as np
import pytest
from src.face.detector import FaceDetector, FaceDetectionResult

SAMPLE_FACE_PATH = "data/samples/sample_sataboris.jpg"


def test_face_detector_initialization():
    detector = FaceDetector()
    assert detector.model_name is not None
    assert detector.det_size == (640, 640)


def test_cosine_similarity():
    detector = FaceDetector()
    emb1 = np.random.randn(512).astype(np.float32)
    emb1 = emb1 / np.linalg.norm(emb1)

    # Identical vector should yield 1.0 similarity
    sim_identical = detector.compute_similarity(emb1, emb1)
    assert pytest.approx(sim_identical, 0.001) == 1.0

    # Orthogonal vector
    emb2 = np.random.randn(512).astype(np.float32)
    emb2 = emb2 / np.linalg.norm(emb2)
    sim_random = detector.compute_similarity(emb1, emb2)
    assert 0.0 <= sim_random <= 1.0


def test_face_detection_real_portrait():
    detector = FaceDetector()
    if not Path(SAMPLE_FACE_PATH).exists():
        from src.download_samples import download_high_quality_test_faces
        download_high_quality_test_faces()

    res = detector.detect_and_encode(SAMPLE_FACE_PATH, save_crop=True, save_overlay=True)
    assert isinstance(res, FaceDetectionResult)
    assert res.detected is True
    assert len(res.bbox) == 4
    assert res.embedding is not None
    assert len(res.embedding) == 512
    assert res.confidence > 0.6
    assert res.crop_path is not None
    assert Path(res.crop_path).exists()
