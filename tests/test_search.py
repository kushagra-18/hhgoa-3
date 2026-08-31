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
