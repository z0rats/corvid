"""Full app-state backup/restore (DB + encryption key + optional access token).

See `service.py` for the export/restore mechanics and
docs/adr/0010-backup-restore-design.md for why restore requires a manual restart
instead of hot-swapping the live DB engine.
"""

from typing import Annotated

from fastapi import APIRouter, File, Form, Response, UploadFile
from pydantic import BaseModel, Field

from app.core.backup.schemas import BackupStatusResponse, RestoreResponse
from app.core.backup.service import export_backup, get_backup_status, restore_backup
from app.core.exceptions import ApplicationError

router = APIRouter(prefix="/api/backup", tags=["Backup"])

_RESTORE_CONFIRMATION_PHRASE = "RESTORE"


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
async def export_endpoint(body: BackupExportRequest) -> Response:
    content, filename = await export_backup(
        include_access_token=body.include_access_token, passphrase=body.passphrase
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
    return await restore_backup(archive_bytes, passphrase=passphrase)
