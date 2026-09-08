"""Full app-state backup/restore (DB + encryption key + optional access token).

See `service.py` for the export/restore mechanics and
docs/adr/0010-backup-restore-design.md for why restore requires a manual restart
instead of hot-swapping the live DB engine.
"""

from typing import Annotated

from fastapi import APIRouter, File, Form, Response, UploadFile
from pydantic import BaseModel, Field

from app.core.alerts.service.alerts_service import raise_alert
from app.core.backup.schemas import BackupStatusResponse, RestoreResponse
from app.core.backup.service import export_backup, get_backup_status, restore_backup
from app.core.database import managed_session
from app.core.dependencies import SessionDep
from app.core.exceptions import ApplicationError

router = APIRouter(prefix="/api/backup", tags=["Backup"])

_RESTORE_CONFIRMATION_PHRASE = "RESTORE"


async def _run_with_failure_alert(op, *, failure_title: str):
    """Run `op()`; on failure, raise a "failed" alert and re-raise.

    Alerts on a raised exception in a fresh session, not the request's `db`:
    that one gets rolled back by `get_db()` once the exception propagates past
    it, which would silently discard the alert row (the WS broadcast/Telegram
    push already happened for real by then and are unaffected, but the row
    wouldn't persist).
    """
    try:
        return await op()
    except Exception as exc:
        async with managed_session() as alert_db:
            await raise_alert(
                alert_db,
                module="backup",
                title=failure_title,
                message=str(exc),
                telegram_category="security",
            )
        raise


class BackupExportRequest(BaseModel):
    include_access_token: bool = Field(
        default=False,
        description="Include data/.access_token, so a restore reproduces the exact same token",
    )
    passphrase: str | None = Field(
        default=None,
        description="If set, encrypts the archive (PBKDF2-derived Fernet key) with this passphrase",
    )


@router.get(
    "/status", response_model=BackupStatusResponse, summary="Whether backup/restore is available"
)
async def status_endpoint() -> BackupStatusResponse:
    return get_backup_status()


@router.post("/export", summary="Download a full backup archive")
async def export_endpoint(body: BackupExportRequest, db: SessionDep) -> Response:
    content, filename = await _run_with_failure_alert(
        lambda: export_backup(
            include_access_token=body.include_access_token, passphrase=body.passphrase
        ),
        failure_title="Backup export failed",
    )

    await raise_alert(
        db,
        module="backup",
        title="Backup exported",
        message=f"A backup archive ({filename}) was downloaded.",
        telegram_category="security",
    )
    media_type = "application/x-gzip" if not body.passphrase else "application/octet-stream"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/restore", response_model=RestoreResponse, summary="Restore from a backup archive")
async def restore_endpoint(
    file: Annotated[
        UploadFile, File(..., description="Backup archive produced by /api/backup/export")
    ],
    confirm: Annotated[
        str, Form(..., description=f'Must be exactly "{_RESTORE_CONFIRMATION_PHRASE}"')
    ],
    passphrase: Annotated[str | None, Form()] = None,
) -> RestoreResponse:
    if confirm != _RESTORE_CONFIRMATION_PHRASE:
        raise ApplicationError(
            f'Restore requires confirm="{_RESTORE_CONFIRMATION_PHRASE}" to proceed - this '
            "overwrites the current database, encryption key, and (optionally) access token.",
            status_code=400,
            error_code="BACKUP_RESTORE_NOT_CONFIRMED",
        )

    archive_bytes = await file.read()
    result = await _run_with_failure_alert(
        lambda: restore_backup(archive_bytes, passphrase=passphrase),
        failure_title="Backup restore failed",
    )

    # No SessionDep here: restore_backup() already replaced the underlying DB
    # file on disk, and per docs/adr/0010-backup-restore-design.md the running
    # process doesn't hot-swap its engine, so whether a *new* connection opened
    # now lands on the pre- or post-restore file depends on unrelated connection-
    # pool state. Either way this row's persistence isn't guaranteed across the
    # restart this response tells the operator to do - but the WS broadcast/
    # Telegram push below fire in real time regardless, which is what actually
    # matters here.
    async with managed_session() as alert_db:
        await raise_alert(
            alert_db,
            module="backup",
            title="Backup restored",
            message=(
                "A backup was restored. Restart the backend for the restored data to take effect."
            ),
            telegram_category="security",
        )
    return result
