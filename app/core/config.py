from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    LMS_API_FACULTIES: str
    LMS_API_CAFEDRAS: str
    API_KEY: str
    REPORT_API_KEY: str

    class Config:
        env_file = ".env"

# All values are loaded from environment variables / .env — never hardcode secrets here.
settings = Settings()