"""Static config for the Instagram profile-metadata lookup feature (Instaloader)."""

import re

PACKAGE_NAME = "instaloader"
API_KEY_NAME = "instagram_session"

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._]{1,30}$")

# Minimum viable session cookie set (verified against the installed Instaloader's
# source): `InstaloaderContext.load_session` reads `csrftoken` directly and raises
# a bare KeyError if it's missing; `sessionid`/`ds_user_id` are what actually
# authenticate the request to Instagram - without them the session behaves like
# an anonymous one.
REQUIRED_SESSION_KEYS = ("sessionid", "csrftoken", "ds_user_id")

# `InstaloaderContext.load_session(username, sessiondata)` takes a username only to
# record it locally (`self.username = username`) - it's never sent to Instagram or
# checked against the cookies, so a fixed placeholder is fine here.
SESSION_OWNER_PLACEHOLDER = "corvid"

ERROR_PROFILE_NOT_FOUND = "INSTAGRAM_PROFILE_NOT_FOUND"
ERROR_SESSION_REQUIRED = "INSTAGRAM_SESSION_REQUIRED"
ERROR_RATE_LIMITED = "INSTAGRAM_RATE_LIMITED"
ERROR_UNAVAILABLE = "INSTAGRAM_UNAVAILABLE"
ERROR_UPSTREAM_CHANGED = "INSTAGRAM_UPSTREAM_CHANGED"

# Phase 2 - followers/followees/posts scan (core/scans ScanRun-based, persisted history).
# Valid scan_type values live as the `ScanType` Literal in instagram_scan_schemas.py.

# Hard caps (spec-required): a very active/followed account could otherwise walk
# tens of thousands of items, multiplying ban risk with nothing gained past a
# representative sample. `NodeIterator`'s own page size is 12-50 depending on
# edge type, so this is checked between items, not just between pages.
SCAN_MAX_ITEMS = 200

# Cooperative deadline checked in the same loop as the cancellation flag - an
# `asyncio.wait_for` around the worker thread would abandon *waiting* on it, but
# the thread itself (blocked in a `requests` call) would keep running regardless,
# so the actual bound has to live inside the loop.
SCAN_WALL_CLOCK_TIMEOUT_SECONDS = 180
