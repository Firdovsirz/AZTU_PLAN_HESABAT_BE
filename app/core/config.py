from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    LMS_API_FACULTIES: str
    LMS_API_CAFEDRAS: str
    API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings(
    DATABASE_URL="postgresql://neondb_owner:npg_5DS1QvcugeFx@ep-still-sunset-afwxwb2v-pooler.c-2.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require",
    SECRET_KEY="E3fF8jh9GQf5eO0gJvPUKbn9OpZ9b8A6Ouh3q6KqFYY",
    LMS_API_FACULTIES="https://api-lms.aztu.edu.az/api/faculties",
    LMS_API_CAFEDRAS="https://api-lms.aztu.edu.az/api/cafedras",
    API_KEY="3fa85f64-5717-4562-b3fc-2c963f66afa6")