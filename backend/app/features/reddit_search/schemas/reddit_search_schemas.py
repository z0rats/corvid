import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.features.reddit_search.service.reddit_search_service import normalize_username


class RedditFilters(BaseModel):
    """Optional filters applied to a Reddit user-history search"""

    subreddit: str | None = Field(default=None, description="Restrict results to a single subreddit")
    date_from: int | None = Field(default=None, description="Only include results at/after this Unix timestamp (seconds)")
    date_to: int | None = Field(default=None, description="Only include results at/before this Unix timestamp (seconds)")
    include_nsfw: bool = Field(default=True, description="Whether to include NSFW posts (posts only, has no effect on comments)")


class RedditCursor(BaseModel):
    """Timestamp-based pagination cursor, mirroring created_utc of the current page's boundary items"""

    before: int | None = Field(default=None, description="Fetch results created before this Unix timestamp")
    after: int | None = Field(default=None, description="Fetch results created after this Unix timestamp")


class ScanRequest(BaseModel):
    """Request to fetch a page of a user's Reddit post/comment history"""

    username: str = Field(..., description="Reddit username to search for (accepts u/, @, or a full profile URL)", min_length=1, max_length=300)
    kind: Literal["posts", "comments"] = Field(..., description="Whether to fetch posts or comments")
    filters: RedditFilters = Field(default_factory=RedditFilters)
    cursor: RedditCursor | None = Field(default=None, description="Pagination cursor for a page beyond the first")
    search_id: int | None = Field(default=None, description="Existing search to append this page to; omit to start a new search")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        username = normalize_username(v)
        if not username:
            raise ValueError("Username cannot be empty")
        return username


class RedditItem(BaseModel):
    """A single persisted post or comment result"""

    kind: str = Field(..., description="'post' or 'comment'")
    reddit_id: str = Field(..., description="Reddit's own base36 post/comment ID")
    subreddit: str = Field(..., description="Subreddit the item was posted in")
    title: str | None = Field(default=None, description="Post title (posts only)")
    body: str | None = Field(default=None, description="Post selftext or comment body")
    score: int = Field(..., description="Upvote score")
    num_comments: int | None = Field(default=None, description="Number of comments (posts only)")
    permalink: str = Field(..., description="Path to the item on reddit.com")
    created_utc: int = Field(..., description="Creation time, Unix seconds")
    over_18: bool = Field(default=False, description="Whether the item is marked NSFW")
    removed: bool = Field(default=False, description="Whether the item appears to have been removed by a moderator")
    deleted: bool = Field(default=False, description="Whether the item appears to have been deleted by its author")
    extra: dict | None = Field(default=None, description="Additional source-specific display fields")

    model_config = ConfigDict(from_attributes=True)


class ScanResponse(BaseModel):
    """Result of fetching one page of a user's Reddit history"""

    search_id: int = Field(..., description="ID of the search this page was persisted under")
    items: list[RedditItem] = Field(..., description="Merged, deduplicated results for this page")
    sources: list[str] = Field(..., description="Which archives responded successfully for this page")
    has_more: bool = Field(..., description="Whether another page is likely available")
    next_cursor: RedditCursor | None = Field(default=None, description="Cursor to fetch the next page, if has_more")


class SearchSummary(BaseModel):
    """Summary of a past search, without its results"""

    id: int = Field(..., description="Search ID")
    username: str = Field(..., description="Username that was searched")
    subreddit_filter: str | None = Field(default=None)
    date_from: int | None = Field(default=None)
    date_to: int | None = Field(default=None)
    include_nsfw: bool = Field(...)
    searched_at: datetime.datetime = Field(..., description="When the search was first started")
    result_count: int = Field(default=0, description="Total posts/comments persisted for this search so far")

    model_config = ConfigDict(from_attributes=True)


class SearchDetail(SearchSummary):
    """Full detail of a past search, including all pages fetched so far"""

    results: list[RedditItem] = Field(default_factory=list, description="All persisted posts/comments for this search")
