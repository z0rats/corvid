import pytest

from app.features.youtube.utils.youtube_url_utils import (
    canonical_video_url,
    extract_video_id,
    is_youtube_video_url,
)

VIDEO_ID = "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    "url",
    [
        f"https://www.youtube.com/watch?v={VIDEO_ID}",
        f"https://youtube.com/watch?v={VIDEO_ID}",
        f"http://www.youtube.com/watch?v={VIDEO_ID}&list=PL123&t=42s",
        f"https://m.youtube.com/watch?v={VIDEO_ID}",
        f"https://music.youtube.com/watch?v={VIDEO_ID}&feature=share",
        f"https://youtu.be/{VIDEO_ID}",
        f"https://youtu.be/{VIDEO_ID}?si=abc123",
        f"https://www.youtube.com/shorts/{VIDEO_ID}",
        f"https://www.youtube.com/embed/{VIDEO_ID}",
        f"https://www.youtube-nocookie.com/embed/{VIDEO_ID}",
        f"https://www.youtube.com/live/{VIDEO_ID}",
        f"  https://youtu.be/{VIDEO_ID}  ",
    ],
)
def test_extract_video_id_accepts_known_url_shapes(url):
    assert extract_video_id(url) == VIDEO_ID
    assert is_youtube_video_url(url) is True


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not a url",
        "https://example.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com.evil.com/watch?v=dQw4w9WgXcQ",
        "https://evil.com/youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/",
        "https://www.youtube.com/watch?v=short",
        "https://www.youtube.com/channel/UC123456789",
        "https://youtu.be/",
    ],
)
def test_extract_video_id_rejects_non_video_urls(url):
    assert extract_video_id(url) is None
    assert is_youtube_video_url(url) is False


def test_canonical_video_url():
    assert canonical_video_url(VIDEO_ID) == f"https://www.youtube.com/watch?v={VIDEO_ID}"
