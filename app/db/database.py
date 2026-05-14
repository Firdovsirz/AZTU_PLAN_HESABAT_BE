import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Load .env
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")

# Clean SSL params from URL (important)
parsed = urlparse(DATABASE_URL)
query_params = parse_qs(parsed.query)

# Remove any SSL-related params
query_params.pop("sslmode", None)
query_params.pop("channel_binding", None)

new_query = urlencode(query_params, doseq=True)
clean_url = urlunparse(parsed._replace(query=new_query))

# Convert to asyncpg format
async_database_url = clean_url.replace(
    "postgresql://",
    "postgresql+asyncpg://"
)

# ❌ NO SSL CONTEXT (IMPORTANT FOR LOCAL DB)
engine = create_async_engine(
    async_database_url,
    echo=True,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()