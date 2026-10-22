import datetime
from urllib.parse import urlsplit

from app.features.telegram_search.service.channel_metrics import (
    compute_metrics,
    extract_indicators,
    to_sampled_post,
    top_posts,
)
from app.features.telegram_search.service.tme_parser import ForwardSource, PreviewPost

DAY = datetime.datetime(2026, 10, 1, tzinfo=datetime.UTC)


def _post(
    id_,
    *,
    day=0,
    views=100,
    text="",
    links=(),
    forwarded_from=None,
    has_media=False,
):
    return PreviewPost(
        id=id_,
        url=f"https://t.me/chan/{id_}",
        date=DAY + datetime.timedelta(days=day),
        views=views,
        text=text,
        links=list(links),
        forwarded_from=forwarded_from,
        has_media=has_media,
        is_service=False,
    )


class TestComputeMetrics:
    def test_views_rate_and_ratios(self):
        posts = [
            _post(1, day=0, views=100, has_media=True),
            _post(2, day=1, views=200, forwarded_from=ForwardSource("Src", "src")),
            _post(3, day=2, views=600),
            _post(4, day=4, views=None),
        ]

        metrics = compute_metrics(posts, "chan", member_count=1000)

        assert metrics.posts_sampled == 4
        assert metrics.first_sampled_at == DAY
        assert metrics.last_post_at == DAY + datetime.timedelta(days=4)
        assert metrics.posts_per_day == 0.75  # 3 intervals over 4 days
        assert metrics.avg_views == 300
        assert metrics.median_views == 200
        assert metrics.max_views == 600
        assert metrics.views_to_members == 0.3
        assert metrics.forwarded_count == 1
        assert metrics.forwarded_ratio == 0.25
        assert metrics.media_ratio == 0.25

    def test_empty_sample_has_no_ratios(self):
        metrics = compute_metrics([], "chan", member_count=None)

        assert metrics.posts_sampled == 0
        assert metrics.avg_views is None
        assert metrics.posts_per_day is None
        assert metrics.forwarded_ratio is None
        assert metrics.views_to_members is None

    def test_forward_sources_group_by_username_then_name_and_fold_hidden(self):
        posts = [
            _post(1, forwarded_from=ForwardSource("News", "news")),
            _post(2, forwarded_from=ForwardSource("News (renamed)", "news")),
            _post(3, forwarded_from=ForwardSource("Private", None)),
            _post(4, forwarded_from=ForwardSource(None, None)),
            _post(5, forwarded_from=ForwardSource(None, None)),
            _post(6, forwarded_from=ForwardSource(None, None)),
        ]

        sources = compute_metrics(posts, "chan", None).top_forward_sources

        assert [(s.name, s.username, s.count) for s in sources] == [
            (None, None, 3),
            ("News", "news", 2),
            ("Private", None, 1),
        ]

    def test_mentions_count_links_and_handles_once_per_post_excluding_self_and_source(self):
        posts = [
            _post(1, text="see @Other and @other", links=["https://t.me/other/5"]),
            _post(
                2,
                text="mail me at someone@example.com",
                links=["https://t.me/third", "https://t.me/joinchat/abc", "https://t.me/addlist/x"],
            ),
            _post(
                3,
                text="our own @chan",
                forwarded_from=ForwardSource("Src", "src"),
                links=["https://t.me/src/9"],
            ),
        ]

        mentions = compute_metrics(posts, "chan", None).top_mentions

        assert {(m.username, m.count) for m in mentions} == {("other", 1), ("third", 1)}


def test_top_posts_ranks_by_views_and_skips_unknown_views():
    posts = [_post(1, views=5), _post(2, views=None), _post(3, views=50), _post(4, views=20)]

    assert [p.id for p in top_posts(posts)] == [3, 4, 1]


def test_sampled_post_truncates_long_text_and_counts_links():
    sampled = to_sampled_post(_post(1, text="x" * 2000, links=["https://a.example"]))

    assert len(sampled.text) == 500
    assert sampled.text.endswith("…")
    assert sampled.link_count == 1


class TestExtractIndicators:
    def test_extracts_from_text_links_and_description_without_telegram_hosts(self):
        posts = [
            _post(1, text="C2 at 203.0.113.7, see CVE-2024-3094", links=["https://evil-c2.net/x"]),
            _post(2, text="join https://t.me/other", links=["https://t.me/other"]),
        ]

        indicators = extract_indicators(posts, "contact: ops@corp.net")

        assert indicators["ips"] == ["203.0.113.7"]
        assert indicators["cves"] == ["CVE-2024-3094"]
        assert set(indicators["urls"]) >= {"https://evil-c2.net/x"}
        assert set(indicators["domains"]) >= {"evil-c2.net"}
        assert indicators["emails"] == ["ops@corp.net"]
        hosts = {urlsplit(url).hostname for url in indicators["urls"]} | set(indicators["domains"])
        assert hosts.isdisjoint({"t.me"})

    def test_nothing_to_extract_is_an_empty_dict(self):
        assert extract_indicators([_post(1, text="")], None) == {}
        assert extract_indicators([_post(1, text="hello world")], None) == {}
