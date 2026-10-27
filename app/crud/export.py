"""Plan / report exports as formal PDF or Excel files.

  * export_my_documents — any signed-in user exports their OWN plans/reports
    (the owner is always taken from the token, never from the request).
  * export_structure    — admins export a faculty, kafedra or department.

Scoping lives here; rendering lives in app.utils.export_documents.
"""
import asyncio
import logging
import re
from datetime import datetime
from typing import Callable

from fastapi import status
from fastapi.responses import JSONResponse, Response
from sqlalchemy import and_, or_
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_model import Activity
from app.models.assessment_model import Assessment
from app.models.cafedra_model import Cafedra
from app.models.department_model import Department
from app.models.duty_model import Duty
from app.models.faculty_model import Faculty
from app.models.hesabat_model import Hesabat
from app.models.plan_model import Plan
from app.models.user_model import User
from app.utils.export_documents import BAKU_TZ, ExportDocument, render_pdf, render_xlsx

logger = logging.getLogger(__name__)

FACULTY_LEVEL_LABEL = "Dekanlıq (fakültə səviyyəsi)"

_MEDIA_TYPES = {
    "pdf": "application/pdf",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
_STRUCTURE_TITLES = {
    "plans": "İş planları",
    "reports": "Hesabatlar",
    "all": "İş planları və hesabatlar",
}
_PERSONAL_TITLES = {
    "plans": "Fərdi iş planı",
    "reports": "Fərdi hesabat",
    "all": "Fərdi iş planı və hesabatı",
}
_FILE_SLUGS = {"plans": "planlar", "reports": "hesabatlar", "all": "plan-hesabat"}

# Azerbaijani alphabetical order, so "Əliyev" sorts after "Eyvazov" rather
# than after "Zeynalov" as plain code-point ordering would put it.
_AZ_ORDER = {
    ch: i
    for i, pair in enumerate([
        "aA", "bB", "cC", "çÇ", "dD", "eE", "əƏ", "fF", "gG", "ğĞ", "hH", "xX",
        "ıI", "iİ", "jJ", "kK", "qQ", "lL", "mM", "nN", "oO", "öÖ", "pP", "rR",
        "sS", "şŞ", "tT", "uU", "üÜ", "vV", "yY", "zZ",
    ])
    for ch in pair
}
_TRANSLIT = str.maketrans({
    "ə": "e", "Ə": "E", "ş": "s", "Ş": "S", "ç": "c", "Ç": "C", "ğ": "g",
    "Ğ": "G", "ı": "i", "İ": "I", "ö": "o", "Ö": "O", "ü": "u", "Ü": "U",
})


def _az_key(text: str | None) -> list[int]:
    return [
        10 + _AZ_ORDER[ch] if ch in _AZ_ORDER else (0 if ch.isspace() else 100 + ord(ch))
        for ch in (text or "")
    ]


def _full_name(user: User) -> str:
    return " ".join(p for p in (user.surname, user.name, user.father_name) if p)


def _to_int(value) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _blank(column):
    return or_(column.is_(None), column == "")


async def _collect_rows(
    db: AsyncSession,
    users: list[User],
    unit_of: Callable[[User], str],
    year: int | None,
) -> tuple[list[dict], list[dict]]:
    """Plan rows and report rows (one per plan serial) for the given users."""
    if not users:
        return [], []
    user_map = {u.fin_kod: u for u in users}
    fin_kods = list(user_map)

    query = select(Plan).where(Plan.fin_kod.in_(fin_kods))
    if year is not None:
        query = query.where(Plan.work_year == year)
    plan_rows = (await db.execute(query.order_by(Plan.work_row_number, Plan.id))).scalars().all()
    if not plan_rows:
        return [], []

    # A plan serial spans one work_plan row (and one hesabat row) per activity.
    grouped: dict[str, list[Plan]] = {}
    for row in plan_rows:
        grouped.setdefault(row.work_plan_serial_number, []).append(row)

    hesabat_rows = (await db.execute(
        select(Hesabat).where(
            Hesabat.work_plan_serial_number.in_(list(grouped)),
            Hesabat.fin_kod.in_(fin_kods),
        )
    )).scalars().all()
    hesabats_by_serial: dict[str, list[Hesabat]] = {}
    for h in hesabat_rows:
        hesabats_by_serial.setdefault(h.work_plan_serial_number, []).append(h)

    codes = {c for c in (_to_int(r.activity_type_code) for r in plan_rows) if c is not None}
    activity_names = {}
    if codes:
        result = await db.execute(
            select(Activity.activity_type_code, Activity.activity_type_name)
            .where(Activity.activity_type_code.in_(codes))
        )
        activity_names = {int(code): name for code, name in result.all()}
    score_names = dict((await db.execute(
        select(Assessment.assessment_score, Assessment.score_name)
    )).all())

    plans, reports = [], []
    for serial, rows in grouped.items():
        first = rows[0]
        user = user_map[first.fin_kod]
        activities = []
        for r in rows:
            # Custom ("Digər") activities have no catalogue entry; fall back to
            # the name stored on the plan row.
            name = activity_names.get(_to_int(r.activity_type_code)) or r.activity_type_name
            if name and name not in activities:
                activities.append(name)
        common = {
            "unit": unit_of(user),
            "full_name": _full_name(user),
            "fin_kod": user.fin_kod,
            "serial": serial,
            "work_year": first.work_year,
            "activities": activities,
        }
        plans.append({
            **common,
            "row_number": first.work_row_number,
            "work_desc": first.work_desc,
            "goal": first.goal,
            "deadline": first.deadline,
            "created_at": first.created_at,
        })

        hs = hesabats_by_serial.get(serial, [])
        is_done = bool(hs) and all(h.done for h in hs)
        is_submitted = any(h.submitted for h in hs)
        # Report fields are written identically to every activity row of a serial.
        h = next((x for x in hs if x.submitted), hs[0] if hs else None)
        score = h.assessment_score if h else None
        reports.append({
            **common,
            "result_indicator": h.result_indicator if h else None,
            "done_percentage": h.done_percentage if h else None,
            "self_score_label": (
                f"{score_names[score]} ({score})" if score in score_names
                else (str(score) if score is not None else None)
            ),
            "admin_score": h.admin_assessment if h else None,
            "ai_score": h.ai_assessment if h else None,
            "duration": h.duration_analysis if h else None,
            "submitted_at": h.submitted_at if h else None,
            "status": "done" if is_done else ("submitted" if is_submitted else "pending"),
            "note": h.note if h else None,
            "has_document": bool(h and h.activity_doc_path),
        })

    def sort_key(row):
        return (
            row["unit"] != FACULTY_LEVEL_LABEL,
            _az_key(row["unit"]),
            _az_key(row["full_name"]),
            row.get("row_number") or 0,
            row["serial"],
        )

    plans.sort(key=sort_key)
    order = {row["serial"]: i for i, row in enumerate(plans)}
    reports.sort(key=lambda r: order[r["serial"]])
    return plans, reports


def _filename(content: str, parts: list[str], fmt: str) -> str:
    slugs = [_FILE_SLUGS[content]]
    for part in parts:
        slug = re.sub(r"[^A-Za-z0-9]+", "-", str(part).translate(_TRANSLIT)).strip("-")
        if slug:
            slugs.append(slug[:60])
    return f"AzTU_{'_'.join(slugs)}_{datetime.now(BAKU_TZ):%Y%m%d}.{fmt}"


async def _file_response(doc: ExportDocument, fmt: str, filename: str) -> Response:
    # Rendering is CPU-bound (large faculties run to hundreds of pages), so it
    # runs off the event loop.
    renderer = render_pdf if fmt == "pdf" else render_xlsx
    data = await asyncio.to_thread(renderer, doc)
    return Response(
        content=data,
        media_type=_MEDIA_TYPES[fmt],
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            # Exports carry personal data; never let a proxy or browser cache them.
            "Cache-Control": "no-store",
        },
    )


def _not_found(message: str) -> JSONResponse:
    return JSONResponse(
        content={"statusCode": 404, "message": message},
        status_code=status.HTTP_404_NOT_FOUND,
    )


def _year_detail(year: int | None) -> tuple[str, str]:
    return ("İcra ili", str(year) if year is not None else "Bütün illər")


async def _name_of(db: AsyncSession, code_column, name_column, code) -> str | None:
    if not code:
        return None
    result = await db.execute(select(name_column).where(code_column == code))
    return result.scalars().first()


async def export_my_documents(
    current_user: dict,
    content: str,
    fmt: str,
    year: int | None,
    db: AsyncSession,
):
    try:
        user = (await db.execute(
            select(User).where(User.fin_kod == current_user["fin_kod"])
        )).scalar_one_or_none()
        if not user:
            return _not_found("İstifadəçi tapılmadı.")

        plans, reports = await _collect_rows(db, [user], lambda _u: "", year)

        details = [("Soyadı, adı, ata adı", _full_name(user)), ("FİN", user.fin_kod)]
        for label, code_col, name_col, code in (
            ("Vəzifə", Duty.duty_code, Duty.duty_name, user.duty_code),
            ("Fakültə", Faculty.faculty_code, Faculty.faculty_name, user.faculty_code),
            ("Kafedra", Cafedra.cafedra_code, Cafedra.cafedra_name, user.cafedra_code),
            ("Struktur bölmə", Department.department_code, Department.department_name, user.department_code),
        ):
            name = await _name_of(db, code_col, name_col, code)
            if name:
                details.append((label, name))
        details.append(_year_detail(year))

        doc = ExportDocument(
            title=_PERSONAL_TITLES[content],
            details=details,
            plans=plans if content in ("plans", "all") else None,
            reports=reports if content in ("reports", "all") else None,
            signer_label="İcraçı",
            signer_name=_full_name(user),
        )
        filename = _filename(content, [user.surname, user.name, year or ""], fmt)
        return await _file_response(doc, fmt, filename)

    except Exception:
        logger.exception("Error exporting personal plans/reports")
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


async def export_structure(
    scope: str,
    code: str,
    content: str,
    fmt: str,
    year: int | None,
    include_cafedras: bool,
    current_user: dict,
    db: AsyncSession,
):
    """Export every member's plans/reports for one structure unit.

    Membership mirrors the structure views: kafedra = users with that
    cafedra_code, department = users with that department_code, faculty =
    dekanat-level users (no kafedra/department), optionally plus every kafedra
    of the faculty grouped under its own heading.
    """
    try:
        multi_unit = False
        if scope == "cafedra":
            cafedra = (await db.execute(
                select(Cafedra).where(Cafedra.cafedra_code == code)
            )).scalar_one_or_none()
            if not cafedra:
                return _not_found("Kafedra tapılmadı.")
            faculty_name = await _name_of(db, Faculty.faculty_code, Faculty.faculty_name, cafedra.faculty_code)
            users_query = select(User).where(User.cafedra_code == code)
            unit_of = lambda _u: cafedra.cafedra_name
            details = [("Fakültə", faculty_name or "—"), ("Kafedra", cafedra.cafedra_name)]
            name_parts = ["kafedra", cafedra.cafedra_name]

        elif scope == "department":
            department = (await db.execute(
                select(Department).where(Department.department_code == code)
            )).scalar_one_or_none()
            if not department:
                return _not_found("Struktur bölmə tapılmadı.")
            users_query = select(User).where(User.department_code == code)
            unit_of = lambda _u: department.department_name
            details = [("Struktur bölmə", department.department_name)]
            name_parts = ["bolme", department.department_name]

        else:
            faculty = (await db.execute(
                select(Faculty).where(Faculty.faculty_code == code)
            )).scalar_one_or_none()
            if not faculty:
                return _not_found("Fakültə tapılmadı.")
            faculty_level = and_(
                User.faculty_code == code,
                _blank(User.cafedra_code),
                _blank(User.department_code),
            )
            cafedra_names = {}
            if include_cafedras:
                cafedra_names = dict((await db.execute(
                    select(Cafedra.cafedra_code, Cafedra.cafedra_name)
                    .where(Cafedra.faculty_code == code)
                )).all())
            membership = (
                or_(faculty_level, User.cafedra_code.in_(list(cafedra_names)))
                if cafedra_names else faculty_level
            )
            users_query = select(User).where(membership)
            unit_of = lambda u: cafedra_names.get(u.cafedra_code, FACULTY_LEVEL_LABEL)
            multi_unit = include_cafedras
            details = [
                ("Fakültə", faculty.faculty_name),
                ("Əhatə", "Fakültə və onun bütün kafedraları" if include_cafedras else "Yalnız fakültə səviyyəsi (dekanlıq)"),
            ]
            name_parts = ["fakulte", faculty.faculty_name]

        users = (await db.execute(users_query)).scalars().all()
        plans, reports = await _collect_rows(db, users, unit_of, year)

        exporter = (await db.execute(
            select(User).where(User.fin_kod == current_user["fin_kod"])
        )).scalar_one_or_none()

        details += [("İstifadəçi sayı", str(len(users))), _year_detail(year)]
        doc = ExportDocument(
            title=_STRUCTURE_TITLES[content],
            details=details,
            plans=plans if content in ("plans", "all") else None,
            reports=reports if content in ("reports", "all") else None,
            multi_person=True,
            multi_unit=multi_unit,
            signer_label="Tərtib etdi",
            signer_name=_full_name(exporter) if exporter else None,
        )
        filename = _filename(content, name_parts + [year or ""], fmt)
        return await _file_response(doc, fmt, filename)

    except Exception:
        logger.exception("Error exporting structure plans/reports")
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
