"""`validate_feed` runs on a user-typed feed URL before it's saved, and
`validate_and_process_icon` on a user-uploaded image."""

import io
import socket

import httpx
import pytest
from PIL import Image

from app.features.newsfeed.utils import fetching
from app.features.newsfeed.utils.validation import (
    validate_and_process_icon,
    validate_feed,
    validate_image_metadata,
    validate_url_format,
)
from tests.conftest import run

RSS = b"""<?xml version="1.0"?>
<rss version="2.0"><channel><title>Sec Blog</title><description>news</description>
<item><title>One</title><link>https://blog.example/1</link></item>
<item><title>Two</title><link>https://blog.example/2</link></item>
</channel></rss>"""

EMPTY_RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>T</title></channel></rss>"""


@pytest.fixture
def dns(monkeypatch):
    table = {"blog.example": "93.184.216.34", "intranet.example": "172.16.0.9"}

    def fake_getaddrinfo(host, *a, **k):
        ip = table.get(host, host)
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 0))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(fetching.settings.security, "allow_private_network_targets", False)


@pytest.fixture
def serve(patch_httpx_transport):
    requested = []

    def _serve(response):
        def handler(req):
            requested.append(str(req.url))
            return response

        patch_httpx_transport(handler)
        return requested

    return _serve


class TestValidateFeed:
    def test_valid_rss_returns_feed_info(self, dns, serve):
        serve(httpx.Response(200, content=RSS))
        ok, err, info = run(validate_feed("https://blog.example/rss"))
        assert ok is True and err is None
        assert info == {
            "title": "Sec Blog",
            "description": "news",
            "version": "rss20",
            "entry_count": 2,
        }

    @pytest.mark.parametrize(
        "url", ["http://intranet.example/rss", "http://127.0.0.1:8000/api", "http://[::1]/"]
    )
    def test_private_targets_never_fetched(self, dns, serve, url):
        requested = serve(httpx.Response(200, content=RSS))
        ok, err, info = run(validate_feed(url))
        assert ok is False and info is None
        assert err == "Feed URL is unreachable or not allowed"
        assert requested == []

    def test_feedparser_never_receives_the_url(self, dns, serve, monkeypatch):
        """Regression: handing feedparser the URL made it fetch via urllib, unguarded."""
        serve(httpx.Response(200, content=RSS))
        seen = []
        real_parse = fetching.feedparser.parse

        def spy(arg, *a, **k):
            seen.append(arg)
            return real_parse(arg, *a, **k)

        monkeypatch.setattr(fetching.feedparser, "parse", spy)
        run(validate_feed("https://blog.example/rss"))
        assert seen == [RSS]

    def test_http_error_reported_as_unreachable(self, dns, serve):
        serve(httpx.Response(500))
        ok, err, _ = run(validate_feed("https://blog.example/rss"))
        assert (ok, err) == (False, "Feed URL is unreachable or not allowed")

    def test_feed_without_entries_rejected(self, dns, serve):
        serve(httpx.Response(200, content=EMPTY_RSS))
        assert run(validate_feed("https://blog.example/rss")) == (
            False,
            "Feed contains no entries",
            None,
        )

    def test_malformed_xml_rejected(self, dns, serve):
        serve(httpx.Response(200, content=b"<html><body>not a feed<p></body>"))
        ok, err, _ = run(validate_feed("https://blog.example/rss"))
        assert ok is False
        assert err

    @pytest.mark.parametrize("url", ["not a url", "/relative/path", "blog.example/rss"])
    def test_malformed_url_rejected_without_fetch(self, serve, url):
        requested = serve(httpx.Response(200, content=RSS))
        assert run(validate_feed(url)) == (False, "Invalid URL format", None)
        assert requested == []


def test_validate_url_format():
    assert validate_url_format("https://a.example/x") == (True, None)
    assert validate_url_format("a.example") == (False, "Invalid URL format")


def _image_bytes(fmt="PNG", size=(200, 100), mode="RGBA"):
    buf = io.BytesIO()
    Image.new(mode, size, (10, 20, 30, 255) if mode == "RGBA" else (10, 20, 30)).save(
        buf, format=fmt
    )
    return buf.getvalue()


class TestIconUpload:
    def test_valid_png_resized_and_converted(self):
        ok, err, result = validate_and_process_icon(_image_bytes(), "logo.png")
        assert ok is True and err is None
        data, name = result
        assert name.endswith(".png")
        img = Image.open(io.BytesIO(data))
        assert img.format == "PNG"
        assert img.mode == "RGB"
        assert max(img.size) == 64
        assert img.size == (64, 32)  # aspect ratio kept

    def test_jpeg_accepted(self):
        ok, _, _ = validate_and_process_icon(_image_bytes("JPEG", mode="RGB"), "logo.jpg")
        assert ok is True

    @pytest.mark.parametrize("name", ["logo.svg", "logo.exe", "logo", "logo.webp"])
    def test_disallowed_extensions_rejected(self, name):
        ok, err, result = validate_and_process_icon(_image_bytes(), name)
        assert ok is False and result is None
        assert err.startswith("Invalid file type")

    def test_oversized_upload_rejected_before_decoding(self):
        ok, err = validate_image_metadata(b"\0" * (5 * 1024 * 1024 + 1), "big.png")
        assert ok is False
        assert "too large" in err

    def test_non_image_with_image_extension_rejected(self):
        ok, err, result = validate_and_process_icon(b"<script>alert(1)</script>", "x.png")
        assert ok is False and result is None
        assert err.startswith("Invalid image file")
