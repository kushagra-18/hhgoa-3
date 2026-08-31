"""
Search providers module with Factory pattern implementation.
"""
from src.search.providers.base import BaseSearchProvider
from src.search.providers.serpapi import SerpApiLensProvider
from src.search.providers.serper import SerperVisualProvider
from src.search.providers.firecrawl import FirecrawlSearchProvider
from src.search.providers.open_web import LiveOpenWebSearchProvider
from src.search.providers.fixture import RealisticFixtureProvider
from src.search.providers.factory import SearchProviderFactory

__all__ = [
    "BaseSearchProvider",
    "SearchProviderFactory",
    "SerpApiLensProvider",
    "SerperVisualProvider",
    "FirecrawlSearchProvider",
    "LiveOpenWebSearchProvider",
    "RealisticFixtureProvider",
]
