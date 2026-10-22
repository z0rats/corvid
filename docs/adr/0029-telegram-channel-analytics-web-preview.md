# Telegram channel analytics read the keyless t.me web preview, not an MTProto user session

Profiling a public Telegram channel (subscribers, activity, reposted sources, links) was borrowed
from MiniOSINT, which does it with Telethon and a logged-in user account. Corvid's existing
Telegram integration is a Bot API notification bot (`docs/adr/0011-telegram-notifications.md`,
`docs/adr/0012-telegram-bot-polling.md`), and the Bot API cannot read channels the bot is not a
member of, so a channel reader needs either an MTProto user session or Telegram's public web
pages. The web pages were checked live (2026-10-22): `t.me/<name>` answers 200 for every valid
name, with a title, exact subscriber or member count and description for a public chat and a
generic "Contact @name" card otherwise; `t.me/s/<name>` serves ~20 posts per page (date, view
count, text, links, forward source) with a `rel="prev"` `?before=<id>` cursor, and redirects to
`t.me/<name>` for groups, users and channels with the preview turned off. Post #1 of a channel is
the "Channel created" service message, so `?before=2` yields the creation date.

## Decision

- `telegram_search` reads only those two public pages: no Telegram account, no API key, no
  session. The client is a fixed-host `httpx` client against `t.me`; only a normalized username
  reaches the path.
- One `ScanFeature` run per channel samples the newest posts (default 100, cap 500, ~0.5 s
  between pages), dedupes by post id, and fetches post #1 for the creation date when the sample
  did not reach it. Cancelling keeps the posts read so far.
- Groups and preview-disabled channels still get a result (the card only, `preview_available:
  false`, no metrics); a user or bot account and a non-existent name fail the run with a clear
  message. A 429 surfaces as "retry in N s".
- Parsing uses BeautifulSoup, already a backend dependency. A missing layout marker raises
  `SourceDriftError`; a weekly canary checks `@durov`'s card and preview.
- Indicators come from the existing `ioc_extractor` over post text, link targets and the
  description, with Telegram's own hosts dropped.

A user session would add a new dependency, a login flow with phone code and 2FA, an encrypted
session file, and a real risk of the account being limited for automated reads - for fields
(exact creation date, per-post forwards, group history) that the keyless pages mostly cover or
that the feature deliberately leaves out of scope (private chats, member lists, people).

## Accepting

- No private channels, no member lists, no group message history: the web preview does not
  serve them.
- Preview view counts are rounded by Telegram (`32.1K`), so view metrics are approximate.
- HTML scraping can drift; the canary and `SourceDriftError` make that visible instead of
  silent, but a layout change breaks the feature until the parser is updated.

## Revisit

- If analysts need group history or channels with the preview turned off often enough to justify
  a burner account: add an optional MTProto session (Telethon, MIT) as a second source, imported
  as a session string rather than a web login, and keep the web preview as the default.

## Rejected

- **MTProto user session (Telethon or Pyrogram) as the only source** - full data, but a new
  dependency, an account-ban risk and a login/session flow, for a single-user self-hosted tool
  whose analysts mostly need what the public pages already show. Pyrogram's upstream is
  additionally unmaintained.
- **Both sources from the start (web preview by default, session when configured)** - doubles
  the parsers, tests and docs before anyone has needed the session-only fields.
- **Bot API** - a bot can only read chats it was added to.
- **Third-party analytics sites (TGStat, Telemetr)** - keyed or paywalled, rate-limited, and
  another party learning which channels the analyst looks at.
