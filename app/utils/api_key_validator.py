import os
from dotenv import load_dotenv
load_dotenv()
from fastapi.security.api_key import APIKeyHeader
from fastapi import HTTPException, status, Security

REPORT_API_KEY = os.getenv('REPORT_API_KEY')
REPORT_API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=REPORT_API_KEY_NAME, auto_error=False)

if not REPORT_API_KEY:
    raise RuntimeError("REPORT_API_KEY environment variable is not set")

def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == REPORT_API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API Key"
        )