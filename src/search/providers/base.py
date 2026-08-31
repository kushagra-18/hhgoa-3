import abc
from typing import List, Optional
from src.search.social_parser import DiscoveredPost


class BaseSearchProvider(abc.ABC):
    """
    Abstract Base Class defining the contract for all Web & Social Media Search Providers.
    """

    @property
    def name(self) -> str:
        """Human-readable provider identifier."""
        return self.__class__.__name__

    @abc.abstractmethod
    def search(self, image_path: str, image_bytes: Optional[bytes] = None) -> List[DiscoveredPost]:
        """
        Execute reverse image or metadata search and return structured DiscoveredPost matches.
        
        :param image_path: Path to the input image or face crop.
        :param image_bytes: Optional raw bytes of the image.
        :return: List of DiscoveredPost instances.
        """
        pass
