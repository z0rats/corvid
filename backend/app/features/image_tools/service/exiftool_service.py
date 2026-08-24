import json
import logging
import shutil
import subprocess
from functools import lru_cache

logger = logging.getLogger(__name__)

EXIFTOOL_TIMEOUT_SECONDS = 10

# Meta fields exiftool -j always includes that aren't tag data, plus filesystem
# tags that - since the image is piped in via stdin, not a real file on disk -
# describe the anonymous pipe (current time, pipe permissions) rather than the
# uploaded file, and would otherwise misleadingly look like real file metadata.
_EXCLUDED_KEYS = {
    "SourceFile",
    "ExifTool:ExifToolVersion",
    "File:FileModifyDate",
    "File:FileAccessDate",
    "File:FileInodeChangeDate",
    "File:FilePermissions",
}


def is_exiftool_available() -> bool:
    return shutil.which("exiftool") is not None


@lru_cache(maxsize=1)
def get_exiftool_version() -> str | None:
    """Return the installed exiftool version, or None if it's not installed."""
    if not is_exiftool_available():
        return None
    try:
        result = subprocess.run(
            ["exiftool", "-ver"],
            capture_output=True,
            text=True,
            timeout=EXIFTOOL_TIMEOUT_SECONDS,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, OSError) as e:
        logger.warning("Error reading exiftool version: %s", e)
        return None


def extract_exiftool_tags(data: bytes) -> dict[str, str] | None:
    """Run exiftool on image bytes (via stdin, no temp file) and return its tags.

    Keys are formatted as "Group Name" (e.g. "EXIF DateTimeOriginal") to match the
    frontend's existing exifread-based grouping. Supplementary/best-effort: returns
    None if exiftool isn't installed or extraction fails for any reason - never
    raises, since this must never block the primary (exifread-based) analysis.
    """
    if not is_exiftool_available():
        return None

    try:
        result = subprocess.run(
            ["exiftool", "-j", "-G", "-a", "-u", "-"],
            input=data,
            capture_output=True,
            timeout=EXIFTOOL_TIMEOUT_SECONDS,
            check=True,
        )
        parsed = json.loads(result.stdout.decode("utf-8", errors="replace"))
        raw_tags = parsed[0]
    except (subprocess.SubprocessError, OSError, json.JSONDecodeError, IndexError) as e:
        logger.warning("Error running exiftool: %s", e)
        return None

    return {
        key.replace(":", " ", 1): str(value)
        for key, value in raw_tags.items()
        if key not in _EXCLUDED_KEYS
    }
