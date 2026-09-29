import datetime

import pytest
from pydantic import ValidationError

from app.features.instagram_search.schemas.instagram_scan_schemas import (
    InstagramScanDetail,
    InstagramScanRequest,
)


@pytest.mark.parametrize("scan_type", ["followers", "followees", "posts"])
def test_accepts_every_valid_scan_type(scan_type):
    request = InstagramScanRequest(username="someuser", scan_type=scan_type)
    assert request.scan_type == scan_type


def test_rejects_an_invalid_scan_type():
    with pytest.raises(ValidationError):
        InstagramScanRequest(username="someuser", scan_type="following")


def test_normalizes_username():
    request = InstagramScanRequest(username="@SomeUser", scan_type="posts")
    assert request.username == "someuser"


def test_rejects_an_invalid_username():
    with pytest.raises(ValidationError):
        InstagramScanRequest(username="bad name!", scan_type="posts")


class _FakeSearch:
    """Stand-in for the InstagramSearch ORM model, including its `items`
    property (see the model's own docstring for why `items` isn't a column)."""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", 1)
        self.scan_type = kwargs.get("scan_type", "posts")
        self.username = kwargs.get("username", "someuser")
        self.mode = kwargs.get("mode", "anonymous")
        self.status = kwargs.get("status", "completed")
        self.item_count = kwargs.get("item_count", 0)
        self.total_count = kwargs.get("total_count")
        self.truncated = kwargs.get("truncated", False)
        self.searched_at = kwargs.get("searched_at")
        self.error = kwargs.get("error")
        self.result = kwargs.get("result")

    @property
    def items(self):
        return self.result or []


def test_detail_reads_items_via_the_models_items_property():
    search = _FakeSearch(result=[{"shortcode": "abc"}], searched_at=datetime.datetime.now())
    detail = InstagramScanDetail.model_validate(search)
    assert detail.items == [{"shortcode": "abc"}]


def test_detail_defaults_items_to_an_empty_list_when_result_is_none():
    search = _FakeSearch(result=None, searched_at=datetime.datetime.now())
    detail = InstagramScanDetail.model_validate(search)
    assert detail.items == []
