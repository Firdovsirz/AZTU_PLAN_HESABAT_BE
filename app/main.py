import os
import logging
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.utils.limiter import register_limiter
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

# --- Logging ---------------------------------------------------------------
# Never run DEBUG in production: it leaks request internals, tokens and OTPs.
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# --- App -------------------------------------------------------------------
# Swagger / ReDoc / OpenAPI schema are fully disabled so the API surface is
# not exposed publicly.
app = FastAPI(
    title="AZTU Plan Hesabat API",
    version="1.0.0",
    description="Backend for AZTU Plan Hesabat system.",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

register_limiter(app)

# NOTE: uploaded report documents contain personal data and are NO LONGER
# served from a public static mount. They are delivered only through the
# authenticated, traversal-safe endpoint GET /api/secure-doc/{serial}/{name}.

# --- CORS ------------------------------------------------------------------
# Restrict to explicitly allowed origins. Wildcard "*" together with
# allow_credentials=True is invalid/insecure, so origins must be listed.
_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-KEY"],
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
