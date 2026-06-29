import os
import logging
from dotenv import load_dotenv

load_dotenv()

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import text

from app.utils.limiter import register_limiter
from app.db.database import engine, Base
from app.models.request_model import Request as RequestModel
from app.models.notification_model import Notification as NotificationModel
from app.models.feedback_model import YouSaidWeDid as FeedbackModel
from app.models.comment_model import Comment as CommentModel
from app.api.v1.routes import (
    auth,
    duty,
    plan,
    user,
    faculty,
    cafedra,
    hesabat,
    request,
    activity,
    assessment,
    department,
    notification,
    feedback,
    comment,
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

# --- Landing page ----------------------------------------------------------
# The root path serves a static HTML page describing the system and crediting
# the developers. Loaded once at import time to avoid disk reads per request.
_INDEX_HTML = (Path(__file__).resolve().parent.parent / "templates" / "index.html").read_text(
    encoding="utf-8"
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root() -> HTMLResponse:
    return HTMLResponse(content=_INDEX_HTML)

# NOTE: uploaded report documents contain personal data and are NO LONGER
# served from a public static mount. They are delivered only through the
# authenticated, traversal-safe endpoint GET /api/secure-doc/{serial}/{name}.

# --- CORS ------------------------------------------------------------------
# Restrict to explicitly allowed origins. Wildcard "*" together with
# allow_credentials=True is invalid/insecure, so origins must be listed.
_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()]

# Always allow the public AzTU sites so the unauthenticated landing/feedback
# endpoints (e.g. GET /api/you-said-we-did) can be fetched from them in the
# browser, even if CORS_ORIGINS is not set in the environment.
_PUBLIC_ALLOWED_ORIGINS = [
    "https://aztu.edu.az",
    "https://www.aztu.edu.az",
]
for _origin in _PUBLIC_ALLOWED_ORIGINS:
    if _origin not in ALLOWED_ORIGINS:
        ALLOWED_ORIGINS.append(_origin)

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
app.include_router(request.router, prefix="/api", tags=["Request"])
app.include_router(notification.router, prefix="/api", tags=["Notification"])
app.include_router(feedback.router, prefix="/api", tags=["Feedback"])
app.include_router(comment.router, prefix="/api", tags=["Comment"])


# --- Schema bootstrap ------------------------------------------------------
# This project does not run migrations; existing tables were created manually.
# `requests` and `notifications` are managed by the app, so create them (and
# only them) idempotently on startup. create_all with checkfirst=True never
# touches tables that already exist. The `requests` table predates the
# target/proposed columns, so they are added with ADD COLUMN IF NOT EXISTS.
@app.on_event("startup")
async def _ensure_schema() -> None:
    try:
        async with engine.begin() as conn:
            await conn.run_sync(
                lambda sync_conn: Base.metadata.create_all(
                    sync_conn,
                    tables=[
                        RequestModel.__table__,
                        NotificationModel.__table__,
                        FeedbackModel.__table__,
                        CommentModel.__table__,
                    ],
                )
            )
            for ddl in (
                "ALTER TABLE requests ADD COLUMN IF NOT EXISTS target_type VARCHAR",
                "ALTER TABLE requests ADD COLUMN IF NOT EXISTS target_serial VARCHAR",
                "ALTER TABLE requests ADD COLUMN IF NOT EXISTS proposed_changes TEXT",
                "ALTER TABLE you_said_we_did ADD COLUMN IF NOT EXISTS you_said_az TEXT",
                "ALTER TABLE you_said_we_did ADD COLUMN IF NOT EXISTS you_said_en TEXT",
                "ALTER TABLE you_said_we_did ADD COLUMN IF NOT EXISTS we_did_az TEXT",
                "ALTER TABLE you_said_we_did ADD COLUMN IF NOT EXISTS we_did_en TEXT",
                "ALTER TABLE you_said_we_did ADD COLUMN IF NOT EXISTS status VARCHAR NOT NULL DEFAULT 'done'",
                # Backfill the bilingual columns from the original single-language
                # columns (only if that 2-column version of the table exists —
                # guarded so it is a no-op on a fresh DB), then drop the obsolete
                # columns whose NOT NULL constraint would otherwise break inserts
                # that only populate the bilingual fields.
                "DO $$ BEGIN "
                "IF EXISTS (SELECT 1 FROM information_schema.columns "
                "WHERE table_name = 'you_said_we_did' AND column_name = 'you_said') "
                "AND EXISTS (SELECT 1 FROM information_schema.columns "
                "WHERE table_name = 'you_said_we_did' AND column_name = 'we_did') THEN "
                "UPDATE you_said_we_did SET "
                "you_said_az = COALESCE(you_said_az, you_said), "
                "you_said_en = COALESCE(you_said_en, you_said), "
                "we_did_az = COALESCE(we_did_az, we_did), "
                "we_did_en = COALESCE(we_did_en, we_did); "
                "END IF; END $$",
                "ALTER TABLE you_said_we_did DROP COLUMN IF EXISTS you_said",
                "ALTER TABLE you_said_we_did DROP COLUMN IF EXISTS we_did",
            ):
                await conn.execute(text(ddl))
    except Exception as exc:  # pragma: no cover - boot-time best effort
        logging.getLogger(__name__).warning(
            "Could not ensure request/notification schema: %s", exc
        )
