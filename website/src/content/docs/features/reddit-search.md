---
title: Reddit Search
description: A Reddit user's full post and comment history, including removed content.
---

Finds a Reddit user's full post and comment history — including content removed by moderators or
deleted by its author — by querying the public Arctic Shift (`arctic-shift.photon-reddit.com`)
and PullPush (`api.pullpush.io`) archive APIs in parallel and merging/deduplicating the results.
No API key required.

Filter by subreddit, date range, or NSFW status, and page through results by post or comment
separately. Pagination is cursor-based on timestamp rather than page number, so paging back and
forth doesn't produce duplicate or skipped rows. Each username investigation is saved to history
so you can revisit it later without re-querying.
