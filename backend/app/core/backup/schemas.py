from pydantic import BaseModel, Field


class BackupStatusResponse(BaseModel):
    supported: bool = Field(description="Whether this deployment's DB backend can be backed up")
    db_dialect: str = Field(description="SQLAlchemy dialect name of the configured database")


class RestoreResponse(BaseModel):
    restart_required: bool = Field(
        default=True,
        description=(
            "Always true today: the restored files take effect only after the backend "
            "process is restarted (docker-entrypoint.py's own startup migration then runs "
            "against them). The currently running process keeps serving the pre-restore "
            "data until then."
        ),
    )
    access_token_restored: bool = Field(
        description="Whether the backup included .access_token, replacing the current one"
    )
