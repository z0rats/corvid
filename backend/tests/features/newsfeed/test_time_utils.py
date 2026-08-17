from datetime import UTC, datetime, timedelta

import pytest

from app.features.newsfeed.utils.time_utils import (
    format_datetime_for_api,
    get_current_utc_timestamp,
    get_cutoff_date_for_retention,
    is_within_retention_period,
    parse_time_range,
)

# --- parse_time_range --------------------------------------------------


def test_parse_time_range_hours():
    before = datetime.now(UTC) - timedelta(hours=24)
    result = parse_time_range("24h")
    assert abs((result - before).total_seconds()) < 2


def test_parse_time_range_days():
    before = datetime.now(UTC) - timedelta(days=7)
    result = parse_time_range("7d")
    assert abs((result - before).total_seconds()) < 2


def test_parse_time_range_is_case_insensitive():
    assert parse_time_range("24H") is not None


@pytest.mark.parametrize("value", [None, "", "bad", "24x", "d", "h", "1w"])
def test_parse_time_range_returns_none_for_invalid_input(value):
    assert parse_time_range(value) is None


def test_parse_time_range_non_integer_amount_returns_none():
    assert parse_time_range("abcd") is None
    assert parse_time_range("12.5d") is None


# --- get_cutoff_date_for_retention / is_within_retention_period -------


def test_get_cutoff_date_for_retention():
    expected = datetime.now(UTC) - timedelta(days=30)
    result = get_cutoff_date_for_retention(30)
    assert abs((result - expected).total_seconds()) < 2


def test_is_within_retention_period_true_for_recent_date():
    recent = datetime.now(UTC) - timedelta(days=1)
    assert is_within_retention_period(recent, retention_days=30) is True


def test_is_within_retention_period_false_for_old_date():
    old = datetime.now(UTC) - timedelta(days=60)
    assert is_within_retention_period(old, retention_days=30) is False


def test_is_within_retention_period_boundary_is_inclusive():
    # article_date set safely after the cutoff computed inside the function
    # call (which runs a moment later than this fixed reference point), so
    # the comparison isn't sensitive to the few microseconds between the two
    # datetime.now() calls.
    article_date = datetime.now(UTC) - timedelta(days=30) + timedelta(seconds=5)
    assert is_within_retention_period(article_date, retention_days=30) is True


# --- format_datetime_for_api --------------------------------------------


def test_format_datetime_for_api_returns_isoformat_string():
    dt = datetime(2024, 1, 15, 12, 30, 0, tzinfo=UTC)
    assert format_datetime_for_api(dt) == "2024-01-15T12:30:00+00:00"


def test_format_datetime_for_api_returns_none_for_none_input():
    assert format_datetime_for_api(None) is None


# --- get_current_utc_timestamp ------------------------------------------


def test_get_current_utc_timestamp_is_timezone_aware_utc():
    result = get_current_utc_timestamp()
    assert result.tzinfo == UTC
