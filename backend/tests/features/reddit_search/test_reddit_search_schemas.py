import pytest
from pydantic import ValidationError

from app.features.reddit_search.schemas.reddit_search_schemas import ScanRequest


class TestScanRequestValidateUsername:
    def test_normalizes_a_full_profile_url(self):
        request = ScanRequest(username="https://www.reddit.com/user/spez/", kind="posts")
        assert request.username == "spez"

    def test_rejects_a_username_that_normalizes_to_empty(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            ScanRequest(username="u/", kind="posts")

    def test_rejects_a_blank_username(self):
        with pytest.raises(ValidationError, match="cannot be empty"):
            ScanRequest(username="   ", kind="posts")

    def test_rejects_an_invalid_kind(self):
        with pytest.raises(ValidationError):
            ScanRequest(username="spez", kind="upvotes")
