"""`FaviconDownloader` follows URLs taken from a user-added feed's HTML and
manifest, so every hop must go through `ssrf_guard`; beyond that, the
strategy order (link rel=icon -> linked manifest -> default manifest ->
common paths) and the blank/oversized-image rejection are what matter."""

import io
import socket

import httpx
import pytest
from PIL import Image

from app.features.newsfeed.utils import favicon_downloader as fd
from app.features.newsfeed.utils.favicon_downloader import FaviconDownloader
from tests.conftest import run

PUBLIC_IP = "93.184.216.34"


def _png(blank=False, size=(32, 32)) -> bytes:
    img = Image.new("RGB", size, (255, 255, 255))
    if not blank:
        for x in range(size[0]):
            for y in range(size[1] // 2):
                img.putpixel((x, y), (0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def dns(monkeypatch):
    table = {"site.example": PUBLIC_IP, "cdn.example": PUBLIC_IP, "internal.example": "10.1.2.3"}

    def fake_getaddrinfo(host, *a, **k):
        if host not in table:
            raise socket.gaierror("unknown")
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (table[host], 0))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    monkeypatch.setattr(fd.settings.security, "allow_private_network_targets", False)
    return table


@pytest.fixture
def serve(patch_httpx_transport):
    """Serve `routes` ({(host, path): Response}); record every requested URL.

    safe_get pins the request to the resolved IP and carries the original
    hostname in the Host header, so routing keys on that header."""
    requested: list[str] = []

    def _serve(routes):
        def handler(req: httpx.Request):
            host = req.headers.get("host", req.url.host)
            requested.append(f"{host}{req.url.path}")
            return routes.get((host, req.url.path), httpx.Response(404))

        patch_httpx_transport(handler)
        return requested

    return _serve


def _html(head: str) -> httpx.Response:
    return httpx.Response(
        200, text=f"<html><head>{head}</head></html>", headers={"content-type": "text/html"}
    )


def _json(doc) -> httpx.Response:
    return httpx.Response(200, json=doc, headers={"content-type": "application/manifest+json"})


def _download(url="https://site.example/feed.xml"):
    async def go():
        d = FaviconDownloader()
        try:
            return await d._download(url)
        finally:
            await d.close()

    return run(go())


def _is_png(data: bytes) -> bool:
    return data.startswith(b"\x89PNG")


class TestStrategies:
    def test_link_rel_icon_from_homepage_wins(self, dns, serve):
        requested = serve(
            {
                ("site.example", "/"): _html('<link rel="shortcut icon" href="/img/fav.png">'),
                ("site.example", "/img/fav.png"): httpx.Response(200, content=_png()),
            }
        )
        ok, data, err = _download()
        assert ok is True and err is None
        assert _is_png(data)
        assert requested == ["site.example/", "site.example/img/fav.png"]

    def test_protocol_relative_icon_href(self, dns, serve):
        serve(
            {
                ("site.example", "/"): _html('<link rel="icon" href="//cdn.example/i.png">'),
                ("cdn.example", "/i.png"): httpx.Response(200, content=_png()),
            }
        )
        ok, _, _ = _download()
        assert ok is True

    def test_linked_manifest_picks_largest_icon(self, dns, serve):
        requested = serve(
            {
                ("site.example", "/"): _html('<link rel="manifest" href="/app.json">'),
                ("site.example", "/app.json"): _json(
                    {
                        "icons": [
                            {"src": "small.png", "sizes": "16x16"},
                            {"src": "big.png", "sizes": "192x192"},
                        ]
                    }
                ),
                ("site.example", "/big.png"): httpx.Response(200, content=_png()),
            }
        )
        ok, _, _ = _download()
        assert ok is True
        assert "site.example/big.png" in requested
        assert "site.example/small.png" not in requested

    def test_default_webmanifest_used_when_html_has_nothing(self, dns, serve):
        serve(
            {
                ("site.example", "/"): _html(""),
                ("site.example", "/site.webmanifest"): _json(
                    {"icons": [{"src": "/m.png", "sizes": "512x512"}]}
                ),
                ("site.example", "/m.png"): httpx.Response(200, content=_png()),
            }
        )
        ok, _, _ = _download()
        assert ok is True

    def test_falls_back_to_common_paths(self, dns, serve):
        requested = serve(
            {("site.example", "/apple-touch-icon.png"): httpx.Response(200, content=_png())}
        )
        ok, _, _ = _download()
        assert ok is True
        assert requested[-1] == "site.example/apple-touch-icon.png"
        assert "site.example/favicon.ico" in requested

    def test_nothing_found(self, dns, serve):
        serve({})
        assert _download() == (False, None, "No icon found")


class TestSafety:
    def test_icon_href_to_private_host_is_never_requested(self, dns, serve):
        requested = serve(
            {
                ("site.example", "/"): _html(
                    '<link rel="icon" href="http://internal.example/secret.png">'
                ),
                ("internal.example", "/secret.png"): httpx.Response(200, content=_png()),
                ("site.example", "/favicon.ico"): httpx.Response(200, content=_png()),
            }
        )
        ok, _, _ = _download()
        assert ok is True  # recovered via the fallback path
        assert not any(r.startswith("internal.example") for r in requested)

    def test_feed_on_private_host_fetches_nothing(self, dns, serve):
        requested = serve({})
        ok, _, err = _download("http://internal.example/rss")
        assert ok is False and err == "No icon found"
        assert requested == []

    def test_oversized_icon_rejected(self, dns, serve, monkeypatch):
        monkeypatch.setattr(FaviconDownloader, "MAX_BYTES", 10)
        serve({("site.example", "/favicon.ico"): httpx.Response(200, content=_png())})
        ok, _, _ = _download()
        assert ok is False


class TestProcessImage:
    def test_blank_icon_rejected(self):
        assert (
            FaviconDownloader._process_image(
                FaviconDownloader.__new__(FaviconDownloader), _png(blank=True)
            )
            is None
        )

    def test_non_image_rejected(self):
        assert (
            FaviconDownloader._process_image(
                FaviconDownloader.__new__(FaviconDownloader), b"<html>"
            )
            is None
        )

    def test_large_icon_downscaled_to_target(self):
        d = FaviconDownloader.__new__(FaviconDownloader)
        out = d._process_image(_png(size=(1024, 1024)))
        assert Image.open(io.BytesIO(out)).size == FaviconDownloader.TARGET_SIZE

    def test_transparent_icon_flattened_onto_white(self):
        img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        for x in range(8):
            for y in range(16):
                img.putpixel((x, y), (255, 0, 0, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        d = FaviconDownloader.__new__(FaviconDownloader)
        out = Image.open(io.BytesIO(d._process_image(buf.getvalue())))
        assert out.mode == "RGB"
        assert out.getpixel((15, 0)) == (255, 255, 255)


def test_download_and_save_writes_png_file(dns, serve, tmp_path):
    serve({("site.example", "/favicon.ico"): httpx.Response(200, content=_png())})
    ok, filename, err = run(
        FaviconDownloader.download_and_save_favicon(
            "https://site.example/", str(tmp_path / "icons")
        )
    )
    assert ok is True and err is None
    assert filename.endswith(".png")
    assert _is_png((tmp_path / "icons" / filename).read_bytes())


def test_download_and_save_reports_failure_without_writing(dns, serve, tmp_path):
    serve({})
    ok, filename, err = run(
        FaviconDownloader.download_and_save_favicon(
            "https://site.example/", str(tmp_path / "icons")
        )
    )
    assert (ok, filename, err) == (False, None, "No icon found")
    assert not (tmp_path / "icons").exists()
