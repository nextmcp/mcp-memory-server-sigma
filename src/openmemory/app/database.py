import os
import logging

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

# load .env file
load_dotenv()


def get_database_url() -> str:
    """
    Determine database URL based on environment.
    
    Priority:
    1. DATABASE_URL environment variable (for local dev with explicit URL)
    2. AWS Secrets Manager (if AWS_REGION and DB_SECRET_NAME are set)
    3. SQLite fallback
    """
    # Check for explicit DATABASE_URL
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        logger.info("Using DATABASE_URL from environment")
        return explicit_url
    
    # Check for AWS configuration
    aws_region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    secret_name = os.getenv("DB_SECRET_NAME")
    
    if aws_region and secret_name:
        logger.info(f"Fetching database credentials from Secrets Manager: {secret_name}")
        try:
            from app.secrets import get_secret, build_database_url_from_secret
            secret = get_secret(aws_region, secret_name)
            db_url = build_database_url_from_secret(secret)
            logger.info("Successfully retrieved database credentials from Secrets Manager")
            return db_url
        except Exception as e:
            logger.error(f"Failed to get credentials from Secrets Manager: {e}", exc_info=True)
            logger.warning("Falling back to SQLite")
    
    # Fallback to SQLite
    sqlite_url = "sqlite:///./openmemory.db"
    logger.info(f"Using SQLite: {sqlite_url}")
    return sqlite_url


DATABASE_URL = get_database_url()

# SQLAlchemy engine & session
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
