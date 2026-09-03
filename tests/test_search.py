import pytest
from src.search.social_parser import DiscoveredPost, SocialPostParser
from src.search.providers import (
    SearchProviderFactory,
    BaseSearchProvider,
    RealisticFixtureProvider,
    LiveOpenWebSearchProvider,
    FirecrawlSearchProvider,
)
from src.search.engine import SearchEngine


def test_social_post_canonical_dict():
    post = DiscoveredPost(
        platform="Twitter/X",
        post_url="https://x.com/sataboris/status/1789234901840192831",
        author_handle="@sataboris",
        author_name="Satoshi Borisov",
        post_caption="Excited to share our latest research on zero-knowledge identity proofs.",
        post_timestamp="2024-05-11T16:42:00Z",
        post_image_url="https://images.unsplash.com/photo-1534528741775",
        post_image_sha256="abc123def456",
        visual_similarity_score=0.95,
    )

    canonical = post.canonical_dict()
    assert canonical["platform"] == "Twitter/X"
    assert canonical["author_handle"] == "@sataboris"
    assert "visual_similarity_score" not in canonical  # volatile metric excluded from canonical payload hash

    json_str = post.canonical_json()
    assert '"author_handle":"@sataboris"' in json_str

    hash1 = post.compute_payload_hash()
    hash2 = post.compute_payload_hash()
    assert hash1 == hash2
    assert len(hash1) == 64


def test_platform_detection():
    assert SocialPostParser.detect_platform("https://twitter.com/user/status/123") == "Twitter/X"
    assert SocialPostParser.detect_platform("https://x.com/user/status/123") == "Twitter/X"
    assert SocialPostParser.detect_platform("https://www.linkedin.com/posts/xyz") == "LinkedIn"
    assert SocialPostParser.detect_platform("https://reddit.com/r/ethereum") == "Reddit"
    assert SocialPostParser.detect_platform("https://github.com/profile") == "GitHub"
    assert SocialPostParser.detect_platform("https://example.com/article") == "Web"


def test_realistic_fixture_search():
    provider = RealisticFixtureProvider()
    results = provider.search("dummy_path.jpg")
    assert len(results) >= 1
    post = results[0]
    assert post.platform in ["Twitter/X", "LinkedIn", "Reddit", "Instagram", "Wikipedia", "GitHub", "Web"]
    assert post.author_name != ""
    assert post.post_url.startswith("http")


def test_search_provider_factory_creation():
    # Test factory instantiation of registered providers
    fixture_provider = SearchProviderFactory.create("fixture")
    assert isinstance(fixture_provider, RealisticFixtureProvider)
    assert fixture_provider.name == "RealisticFixtureProvider"

    open_web_provider = SearchProviderFactory.create("open_web")
    assert isinstance(open_web_provider, LiveOpenWebSearchProvider)
    assert open_web_provider.name == "LiveOpenWebSearchProvider"

    firecrawl_provider = SearchProviderFactory.create("firecrawl")
    assert isinstance(firecrawl_provider, FirecrawlSearchProvider)

    # Test unknown provider error handling
    with pytest.raises(ValueError, match="Unknown search provider"):
        SearchProviderFactory.create("non_existent_provider")


def test_search_provider_factory_custom_registration():
    class CustomTestProvider(BaseSearchProvider):
        def search(self, image_path, image_bytes=None):
            return []

    SearchProviderFactory.register("custom_mock", CustomTestProvider)
    assert "custom_mock" in SearchProviderFactory.list_available_providers()
    instance = SearchProviderFactory.create("custom_mock")
    assert isinstance(instance, CustomTestProvider)


def test_search_provider_factory_enabled_chain():
    enabled = SearchProviderFactory.get_enabled_providers()
    assert len(enabled) >= 2  # at minimum LiveOpenWebSearchProvider and RealisticFixtureProvider
    provider_names = [p.name for p in enabled]
    assert "LiveOpenWebSearchProvider" in provider_names
    assert "RealisticFixtureProvider" in provider_names


def test_similarity_threshold_filtering(monkeypatch):
    """Verify that candidates below SIMILARITY_THRESHOLD (0.70) are filtered out."""
    from unittest.mock import MagicMock
    from src.face.detector import FaceDetectionResult
    import numpy as np

    class MockResponse:
        status_code = 200
        content = b"fake_image_bytes"

    monkeypatch.setattr("requests.get", lambda url, timeout=4: MockResponse())

    class MockProvider(BaseSearchProvider):
        def search(self, image_path, image_bytes=None):
            return [
                DiscoveredPost(
                    platform="Twitter/X",
                    post_url="https://x.com/high_sim",
                    author_handle="@high",
                    author_name="High Match",
                    post_caption="High similarity post",
                    post_timestamp="2024-05-11T10:00:00Z",
                    post_image_url="http://test.com/img1.jpg",
                ),
                DiscoveredPost(
                    platform="LinkedIn",
                    post_url="https://linkedin.com/low_sim",
                    author_handle="@low",
                    author_name="Low Match",
                    post_caption="Low similarity post",
                    post_timestamp="2024-05-11T11:00:00Z",
                    post_image_url="http://test.com/img2.jpg",
                ),
            ]

    # Mock face detector where img1 has 0.85 similarity, img2 has 0.55 similarity
    mock_fd = MagicMock()
    mock_fd.detect_and_encode.return_value = FaceDetectionResult(
        detected=True,
        bbox=[10, 10, 100, 100],
        confidence=0.99,
        embedding=np.zeros((512,), dtype=np.float32),
    )
    mock_fd.compute_similarity.side_effect = [0.85, 0.55]

    engine = SearchEngine(
        face_detector=mock_fd,
        providers=[MockProvider()],
        similarity_threshold=0.70,
    )
    engine._get_reference_profiles = lambda: []

    query_face = FaceDetectionResult(
        detected=True,
        bbox=[0, 0, 50, 50],
        confidence=0.98,
        embedding=np.zeros((512,), dtype=np.float32),
    )

    match = engine.search_for_matching_post("dummy.jpg", query_face)
    assert match.author_name == "High Match"
    assert match.visual_similarity_score == 0.85

    # Low match (0.55) must NOT be in top_candidates because it is below 0.70
    top_cands = match.raw_metadata.get("top_candidates", [])
    assert len(top_cands) == 1
    assert top_cands[0]["author"] == "High Match"
    assert top_cands[0]["similarity"] == 0.85


def test_similarity_threshold_rejection_below_threshold(monkeypatch):
    """Verify that when all candidates are below threshold, No Match Found is returned."""
    from unittest.mock import MagicMock
    from src.face.detector import FaceDetectionResult
    import numpy as np

    class MockResponse:
        status_code = 200
        content = b"fake_image_bytes"

    monkeypatch.setattr("requests.get", lambda url, timeout=4: MockResponse())

    class MockProvider(BaseSearchProvider):
        def search(self, image_path, image_bytes=None):
            return [
                DiscoveredPost(
                    platform="Twitter/X",
                    post_url="https://x.com/sub_threshold",
                    author_handle="@sub",
                    author_name="Sub Threshold Match",
                    post_caption="Sub-threshold post",
                    post_timestamp="2024-05-11T12:00:00Z",
                    post_image_url="http://test.com/img.jpg",
                ),
            ]

    mock_fd = MagicMock()
    mock_fd.detect_and_encode.return_value = FaceDetectionResult(
        detected=True,
        bbox=[10, 10, 100, 100],
        confidence=0.99,
        embedding=np.zeros((512,), dtype=np.float32),
    )
    # Return 0.62 which is below 0.70
    mock_fd.compute_similarity.return_value = 0.62

    engine = SearchEngine(
        face_detector=mock_fd,
        providers=[MockProvider()],
        similarity_threshold=0.70,
    )
    engine._get_reference_profiles = lambda: []

    query_face = FaceDetectionResult(
        detected=True,
        bbox=[0, 0, 50, 50],
        confidence=0.98,
        embedding=np.zeros((512,), dtype=np.float32),
    )

    match = engine.search_for_matching_post("dummy.jpg", query_face)
    assert match.author_name == "No Match Found"
    assert match.visual_similarity_score == 0.0
    assert "70.0%" in match.post_caption
    assert len(match.raw_metadata.get("top_candidates", [])) == 0
