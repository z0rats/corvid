"""URL parsing helpers for YouTube video links."""
import re
from urllib.parse import parse_qs, urlparse

_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_HOST_SUFFIXES = ("youtube.com", "youtube-nocookie.com")


def extract_video_id(url: str) -> str | None:
    """Extract an 11-character YouTube video ID from a video URL, or None if unrecognized.

    Handles youtu.be short links, youtube.com/watch, /shorts/, /embed/, /live/, and the
    m./music./www. subdomains (and the cookie-less youtube-nocookie.com embed host).
    """
    try:
        parsed = urlparse((url or "").strip())
    except ValueError:
        return None

    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]

    if host == "youtu.be":
        candidate = parsed.path.lstrip("/").split("/")[0]
        return candidate if _VIDEO_ID_RE.match(candidate) else None

    if not any(host == suffix or host.endswith(f".{suffix}") for suffix in _HOST_SUFFIXES):
        return None

    if parsed.path == "/watch":
        candidate = parse_qs(parsed.query).get("v", [None])[0]
        return candidate if candidate and _VIDEO_ID_RE.match(candidate) else None

    for prefix in ("/shorts/", "/embed/", "/live/"):
        if parsed.path.startswith(prefix):
            candidate = parsed.path[len(prefix):].split("/")[0]
            return candidate if _VIDEO_ID_RE.match(candidate) else None

    return None


def is_youtube_video_url(url: str) -> bool:
    """Whether `url` is a YouTube URL a video ID can be extracted from."""
    return extract_video_id(url) is not None


def canonical_video_url(video_id: str) -> str:
    """The canonical `youtube.com/watch?v=` URL for a video ID."""
    return f"https://www.youtube.com/watch?v={video_id}"
