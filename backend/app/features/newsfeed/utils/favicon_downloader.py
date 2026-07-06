import asyncio
import logging
import os
import uuid
from urllib.parse import urlsplit, urlunsplit

import httpx
from bs4 import BeautifulSoup
from PIL import Image, ImageStat
import io

from app.core.config.settings import settings
from app.core.security.ssrf_guard import validate_public_url

logger = logging.getLogger(__name__)

class FaviconDownloader:
    """Utility to fetch, process, and save website favicons robustly."""

    COMMON_PATHS = [
        '/favicon.ico',
        '/favicon.png',
        '/apple-touch-icon.png',
        '/apple-touch-icon-precomposed.png',
        '/android-chrome-192x192.png',
        '/android-chrome-512x512.png',
        '/icon-192x192.png',
        '/icon-512x512.png',
        '/site.webmanifest'
    ]
    TARGET_SIZE = (512, 512)
    MAX_BYTES = 2 * 1024 * 1024
    TIMEOUT = 10.0
    BLANK_STDDEV_THRESHOLD = 10  # too low => nearly blank image

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=self.TIMEOUT,
            headers={
                'User-Agent': 'FaviconDownloader/1.0',
                'Accept': 'image/*,application/json;q=0.8,text/html;q=0.5,*/*;q=0.3'
            }
        )

    async def close(self) -> None:
        """Close the HTTP client session."""
        await self._client.aclose()

    @classmethod
    async def download_and_save_favicon(
        cls,
        site_url: str,
        save_dir: str = 'app/static/feedicons'
    ) -> tuple[bool, str | None, str | None]:
        """
        Convenience method: instantiate downloader, fetch & save favicon, then close.
        """
        downloader = cls()
        try:
            return await downloader.download_and_save(site_url, save_dir)
        finally:
            await downloader.close()

    async def download_and_save(
        self,
        site_url: str,
        save_dir: str = 'app/static/feedicons'
    ) -> tuple[bool, str | None, str | None]:
        """Fetch best favicon and save it as a PNG file."""
        try:
            found, raw, err = await self._download(site_url)
            if not found or raw is None:
                return False, None, err
            os.makedirs(save_dir, exist_ok=True)
            filename = f"{uuid.uuid4().hex}.png"
            path = os.path.join(save_dir, filename)
            await asyncio.to_thread(lambda: open(path, 'wb').write(raw))
            logger.info("Saved favicon: %s", filename)
            return True, filename, None
        except Exception as e:
            logger.error("Error saving favicon for %s: %s", site_url, e)
            return False, None, str(e)

    async def _safe_get(self, url: str) -> httpx.Response:
        """GET `url` after validating and pinning it to a non-private IP.

        `feed.url` (and every URL derived from a page's HTML/manifest) is user-supplied,
        so this is an SSRF-prone code path. We resolve the hostname ourselves, reject
        private/loopback/link-local/metadata addresses, and connect directly to the
        vetted IP (Host header + SNI kept as the original hostname) instead of letting
        httpx re-resolve the hostname later, which would reopen a DNS-rebinding gap.
        """
        url = str(url)
        parsed = urlsplit(url)
        ip = validate_public_url(url, allow_private=settings.security.allow_private_network_targets)
        pinned_host = f"[{ip}]" if ":" in ip else ip
        pinned_netloc = f"{pinned_host}:{parsed.port}" if parsed.port else pinned_host
        pinned_url = urlunsplit((parsed.scheme, pinned_netloc, parsed.path or '/', parsed.query, parsed.fragment))
        extensions = {"sni_hostname": parsed.hostname} if parsed.scheme == "https" else {}
        return await self._client.get(pinned_url, headers={"Host": parsed.hostname}, extensions=extensions)

    async def _download(self, site_url: str) -> tuple[bool, bytes | None, str | None]:
        """Try several strategies to locate and download favicon image data."""
        parsed = httpx.URL(site_url)
        base = f"{parsed.scheme}://{parsed.host}"
        home = base + '/'

        # 1. HTML link rel="icon" on homepage
        html_icon = await self._fetch_from_html(home)
        if html_icon:
            ok, data = await self._try_fetch_icon(html_icon, base)
            if ok:
                return True, data, None

        # 2. <link rel="manifest"> in HTML
        manifest_html = await self._fetch_manifest_from_html(home)
        if manifest_html:
            ok, data = await self._try_fetch_icon(manifest_html, base)
            if ok:
                return True, data, None

        # 3. default site.webmanifest JSON
        manifest_default = await self._fetch_manifest_default(parsed)
        if manifest_default:
            ok, data = await self._try_fetch_icon(manifest_default, base)
            if ok:
                return True, data, None

        # 4. common fallback paths
        for path in self.COMMON_PATHS:
            url = base + path
            ok, data = await self._try_fetch_icon(url, base)
            if ok:
                return True, data, None

        return False, None, 'No icon found'

    async def _fetch_from_html(self, url: str) -> str | None:
        """Parse HTML to find <link rel="icon"> href."""
        try:
            resp = await self._safe_get(url)
            if resp.status_code != 200 or 'html' not in resp.headers.get('Content-Type', ''):
                return None
            soup = BeautifulSoup(resp.text, 'lxml')
            for tag in soup.find_all('link', rel=lambda v: v and 'icon' in v.lower()):
                href = tag.get('href')
                if href:
                    return self._normalize_url(href, url)
        except Exception as e:
            logger.debug("HTML parse error at %s: %s", url, e)
        return None

    async def _fetch_manifest_from_html(self, url: str) -> str | None:
        """Parse HTML to find <link rel="manifest"> href and return its JSON 'src'."""
        try:
            resp = await self._safe_get(url)
            if resp.status_code != 200 or 'html' not in resp.headers.get('Content-Type', ''):
                return None
            soup = BeautifulSoup(resp.text, 'lxml')
            tag = soup.find('link', rel=lambda v: v and 'manifest' in v.lower())
            if tag and tag.get('href'):
                manifest_url = self._normalize_url(tag['href'], url)
                # fetch manifest and pick largest icon
                resp2 = await self._safe_get(manifest_url)
                if resp2.status_code == 200 and 'json' in resp2.headers.get('Content-Type', ''):
                    doc = resp2.json()
                    icons = doc.get('icons', [])
                    icons = sorted(
                        icons,
                        key=lambda i: int(i.get('sizes', '0x0').split('x')[0]),
                        reverse=True
                    )
                    if icons and icons[0].get('src'):
                        return self._normalize_url(icons[0]['src'], manifest_url)
        except Exception as e:
            logger.debug("Manifest HTML parse error at %s: %s", url, e)
        return None

    async def _fetch_manifest_default(self, parsed_url: httpx.URL) -> str | None:
        """Fetch /site.webmanifest at root and return largest icon's src."""
        manifest_url = f"{parsed_url.scheme}://{parsed_url.host}/site.webmanifest"
        try:
            resp = await self._safe_get(manifest_url)
            if resp.status_code == 200 and 'json' in resp.headers.get('Content-Type', ''):
                doc = resp.json()
                icons = doc.get('icons', [])
                icons = sorted(
                    icons,
                    key=lambda i: int(i.get('sizes', '0x0').split('x')[0]),
                    reverse=True
                )
                if icons and icons[0].get('src'):
                    return self._normalize_url(icons[0]['src'], manifest_url)
        except Exception as e:
            logger.debug("Default manifest error at %s: %s", manifest_url, e)
        return None

    def _normalize_url(self, href: str, base: str) -> str:
        """Convert href to absolute URL based on base."""
        if href.startswith('//'):
            return f"{httpx.URL(base).scheme}:{href}"
        if href.startswith('http'):
            return href
        return httpx.URL(base).join(href)

    async def _try_fetch_icon(self, icon_url: str, base: str) -> tuple[bool, bytes | None]:
        """Download, validate, and process an icon URL."""
        try:
            resp = await self._safe_get(icon_url)
            if resp.status_code != 200:
                logger.debug("HTTP %s at %s", resp.status_code, icon_url)
                return False, None
            data = resp.content
            if len(data) > self.MAX_BYTES:
                logger.debug("Icon at %s too large: %s bytes", icon_url, len(data))
                return False, None
            processed = await asyncio.to_thread(self._process_image, data)
            if processed:
                logger.info("Fetched and processed icon from %s", icon_url)
                return True, processed
        except Exception as e:
            logger.debug("Fetch icon error at %s: %s", icon_url, e)
        return False, None

    def _process_image(self, data: bytes) -> bytes | None:
        """Load image, reject blank, resize, and return PNG bytes."""
        try:
            img = Image.open(io.BytesIO(data))
            img = img.convert('RGBA')
            bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
            bg.paste(img, mask=img)
            img = bg.convert('RGB')
            # reject nearly blank icons
            gray = img.convert('L')
            stat = ImageStat.Stat(gray)
            if stat.stddev[0] < self.BLANK_STDDEV_THRESHOLD:
                logger.debug("Rejected blank icon")
                return None
            img.thumbnail(self.TARGET_SIZE, Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format='PNG', optimize=True)
            return buf.getvalue()
        except Exception as e:
            logger.debug("Image processing error: %s", e)
            return None
