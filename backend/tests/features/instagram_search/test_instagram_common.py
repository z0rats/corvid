import instaloader
import pytest

from app.core.exceptions import AppHTTPException
from app.features.instagram_search.service.instagram_common import (
    build_loader,
    raise_mapped_instaloader_exception,
)


def test_build_loader_disables_every_download_flag_and_iphone_support():
    loader = build_loader()

    assert loader.context.iphone_support is False


@pytest.mark.parametrize(
    ("exception", "expected_status", "expected_code"),
    [
        (
            instaloader.exceptions.ProfileNotExistsException("nope"),
            404,
            "INSTAGRAM_PROFILE_NOT_FOUND",
        ),
        (
            instaloader.exceptions.LoginRequiredException("login required"),
            401,
            "INSTAGRAM_SESSION_REQUIRED",
        ),
        (
            instaloader.exceptions.PrivateProfileNotFollowedException("private"),
            401,
            "INSTAGRAM_SESSION_REQUIRED",
        ),
        (
            instaloader.exceptions.TooManyRequestsException("429"),
            429,
            "INSTAGRAM_RATE_LIMITED",
        ),
        (
            instaloader.exceptions.ConnectionException("down"),
            503,
            "INSTAGRAM_UNAVAILABLE",
        ),
        (
            instaloader.exceptions.BadResponseException("bad shape"),
            502,
            "INSTAGRAM_UPSTREAM_CHANGED",
        ),
        (
            instaloader.exceptions.QueryReturnedBadRequestException("400"),
            502,
            "INSTAGRAM_UPSTREAM_CHANGED",
        ),
        (
            instaloader.exceptions.QueryReturnedForbiddenException("403"),
            502,
            "INSTAGRAM_UPSTREAM_CHANGED",
        ),
        (
            instaloader.exceptions.QueryReturnedNotFoundException("404"),
            502,
            "INSTAGRAM_UPSTREAM_CHANGED",
        ),
        (
            instaloader.exceptions.InstaloaderException("unexpected"),
            502,
            "INSTAGRAM_UPSTREAM_CHANGED",
        ),
    ],
)
def test_maps_each_instaloader_exception(exception, expected_status, expected_code):
    with pytest.raises(AppHTTPException) as exc_info:
        raise_mapped_instaloader_exception(exception, "someuser")

    assert exc_info.value.status_code == expected_status
    assert exc_info.value.error_code == expected_code


def test_too_many_requests_is_mapped_before_the_broader_connection_exception():
    """TooManyRequestsException subclasses ConnectionException - regression guard
    against the isinstance checks being reordered and losing the 429 mapping."""
    with pytest.raises(AppHTTPException) as exc_info:
        raise_mapped_instaloader_exception(
            instaloader.exceptions.TooManyRequestsException("429"), "someuser"
        )
    assert exc_info.value.status_code == 429


def test_query_returned_not_found_is_mapped_before_the_broader_connection_exception():
    """QueryReturnedNotFoundException subclasses ConnectionException - regression
    guard against it being silently caught by the 503 branch instead of grouped
    with its BadRequest/Forbidden siblings at 502, as instaloader's own exception
    module groups them."""
    with pytest.raises(AppHTTPException) as exc_info:
        raise_mapped_instaloader_exception(
            instaloader.exceptions.QueryReturnedNotFoundException("404"), "someuser"
        )
    assert exc_info.value.status_code == 502
    assert exc_info.value.error_code == "INSTAGRAM_UPSTREAM_CHANGED"


def test_a_non_instaloader_exception_is_reraised_unchanged():
    original = ValueError("not an instaloader exception")
    with pytest.raises(ValueError) as exc_info:
        raise_mapped_instaloader_exception(original, "someuser")
    assert exc_info.value is original
