import datetime

from pydantic import BaseModel, Field


class ActivityItem(BaseModel):
    """One past run/lookup in any feature, as shown in the cross-feature activity feed."""

    feature: str = Field(..., description="Feature that ran it, e.g. 'amass', 'ioc_lookup'")
    id: int = Field(..., description="The run's id within that feature's own history")
    target: str = Field(..., description="What the run was about (username, domain, IOC, ...)")
    status: str = Field(..., description="running, completed, cancelled, or failed")
    timestamp: datetime.datetime = Field(..., description="When the run started (UTC)")
