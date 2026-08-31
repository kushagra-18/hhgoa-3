import logging
from typing import Dict, Type, List, Optional

from src.config import settings
from src.search.providers.base import BaseSearchProvider
from src.search.providers.serpapi import SerpApiLensProvider
from src.search.providers.serper import SerperVisualProvider
from src.search.providers.firecrawl import FirecrawlSearchProvider
from src.search.providers.open_web import LiveOpenWebSearchProvider
from src.search.providers.fixture import RealisticFixtureProvider

logger = logging.getLogger("search_provider.factory")


class SearchProviderFactory:
    """
    Factory class responsible for dynamically registering, instantiating,
    and managing the execution priority of Web & Social Search Providers.
    """

    _registry: Dict[str, Type[BaseSearchProvider]] = {
        "serpapi": SerpApiLensProvider,
        "serper": SerperVisualProvider,
        "firecrawl": FirecrawlSearchProvider,
        "open_web": LiveOpenWebSearchProvider,
        "fixture": RealisticFixtureProvider,
    }

    @classmethod
    def register(cls, name: str, provider_cls: Type[BaseSearchProvider]) -> None:
        """Register a new custom search provider with the factory."""
        key = name.strip().lower()
        cls._registry[key] = provider_cls
        logger.info(f"Registered search provider: '{key}' ({provider_cls.__name__})")

    @classmethod
    def create(cls, name: str, **kwargs) -> BaseSearchProvider:
        """Instantiate a provider by its registered identifier."""
        key = name.strip().lower()
        provider_cls = cls._registry.get(key)
        if not provider_cls:
            raise ValueError(f"Unknown search provider '{name}'. Available: {list(cls._registry.keys())}")
        return provider_cls(**kwargs)

    @classmethod
    def get_enabled_providers(cls) -> List[BaseSearchProvider]:
        """
        Dynamically construct the active provider pipeline based on configured
        environment variables and operational availability.
        """
        active_providers: List[BaseSearchProvider] = []

        # 1. SerpApi Google Lens (if API key configured)
        if settings.SERPAPI_API_KEY:
            active_providers.append(cls.create("serpapi"))

        # 2. Firecrawl AI Web Crawler (if API key configured)
        if settings.FIRECRAWL_API_KEY:
            active_providers.append(cls.create("firecrawl"))

        # 3. Serper Visual Search (if API key configured)
        if settings.SERPER_API_KEY:
            active_providers.append(cls.create("serper"))

        # 4. Live Open Web & Knowledge Graph Provider (Always Active)
        active_providers.append(cls.create("open_web"))

        # 5. Verified Offline Fixture (Fallback)
        active_providers.append(cls.create("fixture"))

        return active_providers

    @classmethod
    def list_available_providers(cls) -> List[str]:
        """Returns all registered provider names."""
        return list(cls._registry.keys())
