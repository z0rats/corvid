from app.features.reddit_search.service.reddit_search_service import (
    _build_urls,
    _get_status,
    _merge_and_sort,
    normalize_username,
    to_result_row,
)

# --- normalize_username ---------------------------------------------------


def test_normalize_username_strips_full_profile_url():
    assert normalize_username("https://www.reddit.com/user/spez/") == "spez"


def test_normalize_username_strips_old_and_new_subdomains():
    assert normalize_username("https://old.reddit.com/u/spez") == "spez"
    assert normalize_username("https://new.reddit.com/u/spez") == "spez"


def test_normalize_username_strips_user_prefix_without_url():
    assert normalize_username("u/spez") == "spez"
    assert normalize_username("/user/spez") == "spez"


def test_normalize_username_strips_leading_at():
    assert normalize_username("@spez") == "spez"


def test_normalize_username_strips_trailing_path_query_fragment():
    assert normalize_username("spez/comments") == "spez"
    assert normalize_username("spez?foo=bar") == "spez"
    assert normalize_username("spez#section") == "spez"


def test_normalize_username_handles_plain_username():
    assert normalize_username("spez") == "spez"


def test_normalize_username_handles_none_and_blank():
    assert normalize_username(None) == ""
    assert normalize_username("   ") == ""


# --- _build_urls ------------------------------------------------------------


def test_build_urls_posts_excludes_nsfw_by_default():
    arctic_url, pullpush_url = _build_urls(
        "spez",
        "posts",
        subreddit=None,
        date_from=None,
        date_to=None,
        include_nsfw=False,
        cursor_before=None,
        cursor_after=None,
    )
    assert "over_18=false" in arctic_url
    assert "over_18=false" in pullpush_url
    assert "posts/search" in arctic_url
    assert "/submission/" in pullpush_url


def test_build_urls_comments_never_include_over_18_filter():
    arctic_url, _ = _build_urls(
        "spez",
        "comments",
        subreddit=None,
        date_from=None,
        date_to=None,
        include_nsfw=False,
        cursor_before=None,
        cursor_after=None,
    )
    assert "over_18" not in arctic_url
    assert "comments/search" in arctic_url


def test_build_urls_cursor_overrides_date_range():
    # Pagination cursors take priority over the original date_from/date_to
    # filters once a user pages past the first screen.
    arctic_url, _ = _build_urls(
        "spez",
        "posts",
        subreddit=None,
        date_from=1000,
        date_to=2000,
        include_nsfw=True,
        cursor_before=1500,
        cursor_after=1200,
    )
    assert "before=1500" in arctic_url
    assert "after=1200" in arctic_url


def test_build_urls_falls_back_to_date_range_without_cursor():
    arctic_url, _ = _build_urls(
        "spez",
        "posts",
        subreddit=None,
        date_from=1000,
        date_to=2000,
        include_nsfw=True,
        cursor_before=None,
        cursor_after=None,
    )
    assert "before=2000" in arctic_url
    assert "after=1000" in arctic_url


def test_build_urls_includes_subreddit_filter_when_given():
    arctic_url, pullpush_url = _build_urls(
        "spez",
        "posts",
        subreddit="python",
        date_from=None,
        date_to=None,
        include_nsfw=True,
        cursor_before=None,
        cursor_after=None,
    )
    assert "subreddit=python" in arctic_url
    assert "subreddit=python" in pullpush_url


# --- _get_status --------------------------------------------------------


def test_get_status_detects_moderator_removed_post():
    removed, deleted = _get_status({"selftext": "[removed]"}, "posts")
    assert removed is True
    assert deleted is False


def test_get_status_detects_removed_by_category_post():
    removed, deleted = _get_status({"selftext": "hello", "removed_by_category": "moderator"}, "posts")
    assert removed is True
    assert deleted is False


def test_get_status_detects_author_deleted_content():
    removed, deleted = _get_status({"body": "irrelevant", "author": "[deleted]"}, "comments")
    assert removed is False
    assert deleted is True


def test_get_status_detects_deleted_body_text():
    removed, deleted = _get_status({"body": "[deleted]", "author": "spez"}, "comments")
    assert removed is False
    assert deleted is True


def test_get_status_normal_content_is_neither():
    removed, deleted = _get_status({"body": "hello world", "author": "spez"}, "comments")
    assert removed is False
    assert deleted is False


# --- _merge_and_sort ------------------------------------------------------


def test_merge_and_sort_dedupes_by_id_arctic_wins_ties():
    arctic = [{"id": "abc123", "created_utc": 100, "source": "arctic"}]
    pullpush = [{"id": "abc123", "created_utc": 100, "source": "pullpush"}]

    merged = _merge_and_sort(arctic, pullpush, "posts", include_nsfw=True)

    assert len(merged) == 1
    assert merged[0]["source"] == "arctic"


def test_merge_and_sort_keeps_distinct_ids_from_both_sources():
    arctic = [{"id": "a1", "created_utc": 100}]
    pullpush = [{"id": "p1", "created_utc": 200}]

    merged = _merge_and_sort(arctic, pullpush, "posts", include_nsfw=True)

    assert {item["id"] for item in merged} == {"a1", "p1"}


def test_merge_and_sort_orders_desc_by_created_utc():
    arctic = [{"id": "old", "created_utc": 100}]
    pullpush = [{"id": "new", "created_utc": 300}, {"id": "mid", "created_utc": 200}]

    merged = _merge_and_sort(arctic, pullpush, "posts", include_nsfw=True)

    assert [item["id"] for item in merged] == ["new", "mid", "old"]


def test_merge_and_sort_missing_created_utc_sorts_last():
    items = [{"id": "has_ts", "created_utc": 500}, {"id": "no_ts"}]

    merged = _merge_and_sort(items, None, "posts", include_nsfw=True)

    assert [item["id"] for item in merged] == ["has_ts", "no_ts"]


def test_merge_and_sort_filters_nsfw_posts_client_side_for_pullpush():
    # Arctic already applies the over_18 filter server-side; PullPush does not,
    # so the merge step must drop NSFW PullPush posts when include_nsfw=False.
    arctic = [{"id": "a1", "created_utc": 100, "over_18": False}]
    pullpush = [
        {"id": "p1", "created_utc": 200, "over_18": False},
        {"id": "p2", "created_utc": 300, "over_18": True},
    ]

    merged = _merge_and_sort(arctic, pullpush, "posts", include_nsfw=False)

    assert {item["id"] for item in merged} == {"a1", "p1"}


def test_merge_and_sort_does_not_filter_nsfw_for_comments():
    # Comments have no over_18 field, so the filter must be a no-op there
    # even when include_nsfw=False, or every comment would be silently dropped.
    comments = [{"id": "c1", "created_utc": 100}]

    merged = _merge_and_sort(comments, None, "comments", include_nsfw=False)

    assert len(merged) == 1


def test_merge_and_sort_skips_items_without_an_id():
    items = [{"created_utc": 100}, {"id": "keep", "created_utc": 200}]

    merged = _merge_and_sort(items, None, "posts", include_nsfw=True)

    assert [item.get("id") for item in merged] == ["keep"]


def test_merge_and_sort_handles_both_sources_missing():
    assert _merge_and_sort(None, None, "posts", include_nsfw=True) == []


# --- to_result_row ----------------------------------------------------------


def test_to_result_row_maps_post_fields():
    item = {
        "id": "abc123",
        "subreddit": "python",
        "title": "Hello",
        "selftext": "body text",
        "score": 42,
        "num_comments": 3,
        "permalink": "/r/python/comments/abc123",
        "created_utc": 1700000000,
        "over_18": False,
        "domain": "self.python",
        "is_self": True,
        "link_flair_text": None,
        "distinguished": None,
        "spoiler": False,
    }

    row = to_result_row(item, "posts")

    assert row["kind"] == "post"
    assert row["reddit_id"] == "abc123"
    assert row["body"] == "body text"
    assert row["num_comments"] == 3
    assert row["removed"] is False
    assert row["deleted"] is False
    assert row["extra"]["domain"] == "self.python"


def test_to_result_row_maps_comment_fields_and_omits_num_comments():
    item = {
        "id": "cmt1",
        "subreddit": "python",
        "body": "a reply",
        "score": 5,
        "permalink": "/r/python/comments/abc/cmt1",
        "created_utc": 1700000000,
        "author": "[deleted]",
    }

    row = to_result_row(item, "comments")

    assert row["kind"] == "comment"
    assert row["title"] is None
    assert row["body"] == "a reply"
    assert row["num_comments"] is None
    assert row["deleted"] is True


def test_to_result_row_defaults_missing_optional_fields():
    row = to_result_row({"id": "x"}, "posts")

    assert row["subreddit"] == ""
    assert row["permalink"] == ""
    assert row["score"] == 0
    assert row["created_utc"] == 0
    assert row["over_18"] is False
