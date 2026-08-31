from pathlib import Path
import pytest
from src.pipeline import FaceVerificationPipeline, PipelineResult

SAMPLE_FACE_PATH = "data/samples/sample_sataboris.jpg"


def test_full_pipeline_run():
    pipeline = FaceVerificationPipeline()

    if not Path(SAMPLE_FACE_PATH).exists():
        from src.download_samples import download_high_quality_test_faces
        download_high_quality_test_faces()

    res = pipeline.run(image_input=SAMPLE_FACE_PATH, save_db=True)
    assert isinstance(res, PipelineResult)
    assert res.success is True
    assert res.face_scan is not None
    assert res.search_match is not None
    assert res.blockchain_attestation is not None
    assert res.verification is not None
    assert res.verification["is_valid"] is True
    assert res.elapsed_seconds > 0
