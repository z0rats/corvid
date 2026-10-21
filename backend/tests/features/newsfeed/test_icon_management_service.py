"""Feed icon lifecycle: upload save, delete-with-favicon-fallback, refetch,
and the startup bulk refetch for feeds still on the default icon."""

import asyncio
import io
from datetime import UTC, datetime

import pytest
from PIL import Image
from sqlalchemy import select

from app.features.newsfeed.models.newsfeed_models import NewsArticle, NewsfeedSettings
from app.features.newsfeed.service import icon_management_service as svc
from app.features.newsfeed.utils.favicon_downloader import FaviconDownloader
from tests.conftest import run


@pytest.fixture
def icons_dir(tmp_path, monkeypatch):
    d = tmp_path / "feedicons"
    monkeypatch.setattr(svc, "ICONS_DIR", str(d))
    return d


@pytest.fixture
def factory(make_session_factory):
    return make_session_factory([NewsfeedSettings.__table__, NewsArticle.__table__])


@pytest.fixture
def downloader(monkeypatch):
    """Replace the network favicon download; `results[feed_url]` is the outcome."""
    results: dict[str, tuple] = {}
    calls: list[str] = []

    async def fake(url, save_dir="ignored"):
        calls.append(url)
        await asyncio.sleep(0)  # yield, as the real network call would
        outcome = results.get(url, (False, None, "No icon found"))
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(FaviconDownloader, "download_and_save_favicon", staticmethod(fake))
    return results, calls


def _png(mode="RGBA"):
    buf = io.BytesIO()
    Image.new(mode, (8, 8), (255, 0, 0, 128) if mode == "RGBA" else (255, 0, 0)).save(
        buf, format="PNG"
    )
    return buf.getvalue()


async def _seed(factory, *feeds, articles=()):
    async with factory() as db:
        db.add_all(list(feeds) + list(articles))
        await db.commit()


async def _feed(factory, name):
    async with factory() as db:
        return (
            await db.execute(select(NewsfeedSettings).where(NewsfeedSettings.name == name))
        ).scalar_one()


class TestSaveIcon:
    def test_saves_png_and_flattens_alpha(self, icons_dir):
        ok, err = run(svc.save_icon(_png(), "abc"))
        assert (ok, err) == (True, None)
        img = Image.open(icons_dir / "abc.png")
        assert img.mode == "RGB"

    def test_keeps_existing_png_suffix(self, icons_dir):
        run(svc.save_icon(_png("RGB"), "x.png"))
        assert (icons_dir / "x.png").exists()
        assert not (icons_dir / "x.png.png").exists()

    def test_invalid_bytes_report_error(self, icons_dir):
        ok, err = run(svc.save_icon(b"nope", "bad"))
        assert ok is False
        assert err.startswith("Error saving icon")


@pytest.mark.parametrize(
    ("name", "size", "ok"),
    [
        ("a.png", 10, True),
        ("A.ICO", 10, True),
        ("a.svg", 10, False),
        ("a.png", 5 * 1024 * 1024 + 1, False),
    ],
)
def test_validate_icon_file(name, size, ok):
    assert svc.validate_icon_file(b"\0" * size, name)[0] is ok


def test_remove_existing_icon(tmp_path):
    f = tmp_path / "i.png"
    f.write_bytes(b"x")
    assert svc.remove_existing_icon(str(f)) is True
    assert not f.exists()
    assert svc.remove_existing_icon(str(f)) is False


class TestDeleteWithFallback:
    def test_favicon_found_replaces_icon_and_syncs_articles(self, factory, icons_dir, downloader):
        results, _ = downloader
        icons_dir.mkdir()
        (icons_dir / "custom.png").write_bytes(b"old")
        results["https://f.example/rss"] = (True, "fresh.png", None)
        run(
            _seed(
                factory,
                NewsfeedSettings(
                    name="f", url="https://f.example/rss", icon="custom.png", icon_id="custom.png"
                ),
                articles=[
                    NewsArticle(
                        feedname="f",
                        icon="custom.png",
                        title="t",
                        summary="s",
                        link="l1",
                        date=datetime(2026, 1, 1, tzinfo=UTC),
                    )
                ],
            )
        )

        async def go():
            async with factory() as db:
                out = await svc.delete_feed_icon_with_favicon_fallback(db, "f")
                await db.commit()
                return out

        ok, msg = run(go())
        assert ok is True
        assert "fresh.png" in msg
        assert not (icons_dir / "custom.png").exists()

        async def check():
            feed = await _feed(factory, "f")
            async with factory() as db:
                art = (await db.execute(select(NewsArticle))).scalar_one()
            return feed, art

        feed, art = run(check())
        assert (feed.icon, feed.icon_id) == ("fresh.png", "fresh.png")
        assert art.icon == "fresh.png"

    def test_no_favicon_falls_back_to_default(self, factory, icons_dir, downloader):
        """Regression: the fallback set the NOT NULL icon_id to None and the flush failed."""
        run(
            _seed(
                factory,
                NewsfeedSettings(
                    name="f", url="https://f.example/rss", icon="custom.png", icon_id="custom.png"
                ),
            )
        )

        async def go():
            async with factory() as db:
                out = await svc.delete_feed_icon_with_favicon_fallback(db, "f")
                await db.commit()
                return out, await _feed(factory, "f")

        (ok, msg), feed = run(go())
        assert ok is True
        assert msg == "Icon deleted, using default icon"
        assert feed.icon == "default.png"
        assert feed.icon_id and feed.icon_id != "custom.png"

    def test_unknown_feed(self, factory, downloader):
        async def go():
            async with factory() as db:
                return await svc.delete_feed_icon_with_favicon_fallback(db, "nope")

        assert run(go()) == (False, "Feed not found")


class TestRefetch:
    def test_success(self, factory, icons_dir, downloader):
        results, _ = downloader
        results["https://f.example/rss"] = (True, "new.png", None)
        run(_seed(factory, NewsfeedSettings(name="f", url="https://f.example/rss")))

        async def go():
            async with factory() as db:
                out = await svc.refetch_feed_favicon(db, "f")
                await db.commit()
                return out, await _feed(factory, "f")

        out, feed = run(go())
        assert out == (True, "Favicon downloaded successfully", "new.png")
        assert feed.icon == "new.png"

    @pytest.mark.parametrize(
        ("outcome", "prefix"),
        [
            ((False, None, "No icon found"), "Could not download favicon: No icon found"),
            (RuntimeError("boom"), "Error downloading favicon: boom"),
        ],
    )
    def test_failure_leaves_feed_untouched(self, factory, downloader, outcome, prefix):
        results, _ = downloader
        results["https://f.example/rss"] = outcome
        run(_seed(factory, NewsfeedSettings(name="f", url="https://f.example/rss")))

        async def go():
            async with factory() as db:
                return await svc.refetch_feed_favicon(db, "f"), await _feed(factory, "f")

        (ok, msg, icon), feed = run(go())
        assert (ok, msg, icon) == (False, prefix, None)
        assert feed.icon == "default.png"


class TestBulkFetch:
    def test_every_default_icon_feed_gets_its_favicon(self, factory, downloader):
        """Each feed's DB update must land even though downloads run concurrently."""
        results, calls = downloader
        feeds = [NewsfeedSettings(name=f"f{i}", url=f"https://f{i}.example/rss") for i in range(4)]
        feeds.append(
            NewsfeedSettings(
                name="custom", url="https://c.example/rss", icon="c.png", icon_id="c.png"
            )
        )
        for i in range(4):
            results[f"https://f{i}.example/rss"] = (True, f"icon{i}.png", None)
        run(_seed(factory, *feeds))

        async def go():
            async with factory() as db:
                await svc.bulk_fetch_favicons_parallel(db)
                await db.commit()
            async with factory() as db:
                rows = (await db.execute(select(NewsfeedSettings))).scalars().all()
                return {r.name: r.icon for r in rows}

        icons = run(go())
        assert icons == {
            "f0": "icon0.png",
            "f1": "icon1.png",
            "f2": "icon2.png",
            "f3": "icon3.png",
            "custom": "c.png",
        }
        assert "https://c.example/rss" not in calls

    def test_nothing_to_do(self, factory, downloader):
        _, calls = downloader

        async def go():
            async with factory() as db:
                await svc.bulk_fetch_favicons_parallel(db)

        run(go())
        assert calls == []
