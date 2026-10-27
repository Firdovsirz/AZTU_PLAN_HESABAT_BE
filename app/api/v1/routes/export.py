from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.utils.limiter import limiter
from app.utils.jwt_required import token_required
from app.crud.export import export_my_documents, export_structure

router = APIRouter()

_ADMIN_ROLES = [0, 1]
_ALL_ROLES = [0, 1, 2, 3, 4]

ExportContent = Literal["plans", "reports", "all"]
ExportFormat = Literal["pdf", "xlsx"]


# Every role exports its own plans/reports; the owner comes from the token.
@router.get("/export/my")
@limiter.limit("30/minute")
async def export_my_endpoint(
    request: Request,
    content: ExportContent = Query("all", description="plans | reports | all"),
    fmt: ExportFormat = Query("pdf", alias="format", description="pdf | xlsx"),
    year: int | None = Query(None, ge=2000, le=2100, description="Filter by plan work year"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(token_required(_ALL_ROLES)),
):
    return await export_my_documents(current_user, content, fmt, year, db)


# Admins export a whole faculty, kafedra or department.
@router.get("/export/structure")
@limiter.limit("30/minute")
async def export_structure_endpoint(
    request: Request,
    scope: Literal["faculty", "cafedra", "department"] = Query(...),
    code: str = Query(..., min_length=1, max_length=64),
    content: ExportContent = Query("all", description="plans | reports | all"),
    fmt: ExportFormat = Query("pdf", alias="format", description="pdf | xlsx"),
    year: int | None = Query(None, ge=2000, le=2100, description="Filter by plan work year"),
    include_cafedras: bool = Query(True, description="Faculty scope only: also export its kafedras"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(token_required(_ADMIN_ROLES)),
):
    return await export_structure(scope, code, content, fmt, year, include_cafedras, current_user, db)
