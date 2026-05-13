import os
from dotenv import load_dotenv

load_dotenv()

import secrets
from fastapi.staticfiles import StaticFiles
from app.utils.limiter import register_limiter
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

from app.api.v1.routes import (
    auth,
    duty,
    plan,
    user,
    faculty,
    cafedra,
    hesabat,
    activity,
    assessment,
    department
)

app = FastAPI(
    title="AZTU Plan Hesabat API",
    version="1.0.0",
    description="Backend for AZTU Plan Hesabat system."
)

register_limiter(app)

import logging

logging.basicConfig(
    level=logging.DEBUG,  # or INFO if you don’t want too much noise
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(faculty.router, prefix="/api", tags=["Faculty"])
app.include_router(cafedra.router, prefix="/api", tags=["Cafedra"])
app.include_router(department.router, prefix="/api", tags=["Department"])
app.include_router(duty.router, prefix="/api", tags=["Duty"])
app.include_router(activity.router, prefix="/api", tags=["Activity"])
app.include_router(assessment.router, prefix="/api", tags=["Assessment"])
app.include_router(plan.router, prefix="/api", tags=["Plan"])
app.include_router(user.router, prefix="/api", tags=["User"])
app.include_router(hesabat.router, prefix="/api", tags=["Hesabat"])

security = HTTPBasic()

SWAGGER_USERNAME = os.getenv("SWAGGER_USERNAME", "sonoma")
SWAGGER_PASSWORD = os.getenv("SWAGGER_PASSWORD", "Sonoma89!&")

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, SWAGGER_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, SWAGGER_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/docs", include_in_schema=False)
def get_documentation(username: str = Depends(get_current_username)):
    return get_swagger_ui_html(openapi_url=app.openapi_url, title="docs")

@app.get("/redoc", include_in_schema=False)
def get_redoc(username: str = Depends(get_current_username)):
    return get_redoc_html(openapi_url=app.openapi_url, title="redoc")