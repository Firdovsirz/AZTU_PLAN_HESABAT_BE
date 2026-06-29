import asyncio
import logging
from datetime import datetime

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.templating import Jinja2Templates

from app.models.user_model import User
from app.models.notification_model import Notification
from app.utils.email import send_html_email

logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="templates")

# Map the in-app notification type onto an e-mail subject prefix.
_SUBJECTS = {
    "success": "Bildiriş",
    "error": "Bildiriş",
    "info": "Bildiriş",
}


def add_notification(
    db: AsyncSession,
    fin_kod: str,
    title: str,
    body: str,
    ntype: str = "info",
) -> Notification:
    """Stage a notification row on the session WITHOUT committing.

    Use this when the notification must be persisted atomically together with
    another change in the same transaction; the caller is responsible for the
    commit. For the common case use ``notify_user`` which also sends the email.
    """
    note = Notification(
        fin_kod=fin_kod,
        title=title,
        body=body,
        type=ntype if ntype in ("success", "error", "info") else "info",
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.add(note)
    return note


async def notify_user(
    db: AsyncSession,
    fin_kod: str,
    title: str,
    body: str,
    ntype: str = "info",
    reason: str | None = None,
) -> None:
    """Persist an in-app notification and e-mail the user.

    The notification (plus anything else already staged on ``db``) is committed
    here, so callers should stage their domain changes first and then call this
    once. E-mail delivery is best-effort and never raises.
    """
    add_notification(db, fin_kod, title, body, ntype)
    await db.commit()

    # E-mail is best-effort: a delivery failure must not undo the committed
    # change or surface as a 500 to the admin who triggered it.
    try:
        fetched_user = await db.execute(select(User).where(User.fin_kod == fin_kod))
        user = fetched_user.scalar_one_or_none()
        if not user or not user.email:
            return

        html_content = templates.get_template("/email/notification_email.html").render(
            {
                "name": user.name,
                "title": title,
                "message": body,
                "reason": reason,
            }
        )
        subject = _SUBJECTS.get(ntype, "Bildiriş")
        # send_html_email is blocking (smtplib); keep the event loop responsive.
        await asyncio.to_thread(
            send_html_email, subject, user.email, user.name, html_content
        )
    except Exception:
        logger.warning("Failed to send notification e-mail to %s", fin_kod, exc_info=True)
