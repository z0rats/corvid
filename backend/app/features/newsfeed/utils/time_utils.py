from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


def parse_time_range(time_range: str) -> datetime | None:
    """
    Parse a relative time range string and return the corresponding cutoff date.
    Supports formats like '24h', '2d', '7d', '14d', '30d'.
    Returns None for invalid formats instead of raising an error directly.
    """
    if not time_range:
        return None
        
    time_range = time_range.lower()
    
    try:
        if time_range.endswith('h'):
            hours = int(time_range[:-1])
            return datetime.now(timezone.utc) - timedelta(hours=hours)
        elif time_range.endswith('d'):
            days = int(time_range[:-1])
            return datetime.now(timezone.utc) - timedelta(days=days)
        else:
            return None
    except ValueError:
        return None


def get_cutoff_date_for_retention(retention_days: int) -> datetime:
    """Calculate cutoff date based on retention period"""
    return datetime.now(timezone.utc) - timedelta(days=retention_days)


def is_within_retention_period(article_date: datetime, retention_days: int) -> bool:
    """Check if article date is within retention period"""
    cutoff_date = get_cutoff_date_for_retention(retention_days)
    return article_date >= cutoff_date


def format_datetime_for_api(dt: datetime) -> str:
    """Format datetime for API response"""
    return dt.isoformat() if dt else None


def get_current_utc_timestamp() -> datetime:
    """Get current UTC timestamp"""
    return datetime.now(timezone.utc)
