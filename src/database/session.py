import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from src.config import settings

logger = logging.getLogger("database")

def get_engine_and_url():
    db_url = settings.DATABASE_URL
    is_sqlite = db_url.startswith("sqlite")
    
    connect_args = {}
    if is_sqlite:
        connect_args = {"check_same_thread": False}
    
    eng = create_engine(
        db_url,
        echo=False,
        connect_args=connect_args,
        pool_pre_ping=True if not is_sqlite else False
    )
    return eng, is_sqlite

engine, is_sqlite_db = get_engine_and_url()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database extensions and tables."""
    from src.database.models import Base

    try:
        with engine.connect() as conn:
            if not is_sqlite_db:
                # Enable pgvector extension if using PostgreSQL
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    conn.commit()
                    logger.info("pgvector extension initialized.")
                except Exception as e:
                    logger.warning(f"Could not enable pgvector extension: {e}")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        raise


def get_db_session() -> Generator[Session, None, None]:
    """Dependency for obtaining database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
