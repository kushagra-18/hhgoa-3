import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    APP_NAME: str = "HH Goa Face-to-Blockchain Pipeline"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = BASE_DIR / "models"
    UPLOADS_DIR: Path = DATA_DIR / "uploads"
    CROPS_DIR: Path = DATA_DIR / "crops"
    CACHE_DIR: Path = DATA_DIR / "cache"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgrespassword@localhost:5432/face_verification_db"
    
    # InsightFace Model Config
    INSIGHTFACE_MODEL_NAME: str = "buffalo_l"
    INSIGHTFACE_DET_SIZE: int = 640
    INSIGHTFACE_CTX_ID: int = 0

    # Blockchain Config
    BLOCKCHAIN_RPC_URL: str = ""
    BLOCKCHAIN_NETWORK_NAME: str = "EVM-Local-Anchor"
    BLOCKCHAIN_PRIVATE_KEY: str = ""
    BLOCKCHAIN_CONTRACT_ADDRESS: str = ""

    # Search & Crawling APIs
    SERPAPI_API_KEY: str = ""
    SERPER_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    FIRECRAWL_API_KEY: str = ""
    GOOGLE_VISION_API_KEY: str = ""

    # Face Match Similarity Threshold (default: 0.70 / 70%)
    SIMILARITY_THRESHOLD: float = 0.70

    @field_validator("SIMILARITY_THRESHOLD", mode="before")
    @classmethod
    def parse_similarity_threshold(cls, v):
        if v is None:
            return 0.70
        try:
            val = float(v)
            if val > 1.0:
                val = val / 100.0
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.70

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def init_directories(self) -> None:
        """Ensure all required runtime data directories exist."""
        for path in [self.DATA_DIR, self.MODELS_DIR, self.UPLOADS_DIR, self.CROPS_DIR, self.CACHE_DIR]:
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.init_directories()
