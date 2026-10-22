# Username candidates from an email are generated in the browser and offered by Username Search

Analysts retype an email's local part into Username Search by hand, and a palette pivot such as
`j.doe+news@gmail.com username` ran Maigret on the whole address, which almost never matches an
account. Two things had to be settled: where the candidate logic lives, and where the candidates
appear. Username Search's `SearchForm` already derives heuristic variants from a typed handle
(`utils/usernameVariants.ts`, which already stripped a `+tag` from a pasted email). Every way into
Username Search with a value (palette pivots, `ChainActionButton`, history pivots) goes through
`?q=` and `usePrefillFromQuery`.

## Decision

- A pure TypeScript function, `features/username-search/utils/emailUsernames.ts`, turns an email
  into ordered candidates: the local part as-is, the same without `+tag`, the dotless form for
  `gmail.com`/`googlemail.com` only, then `_`/``/`-`/`.` separator variants of a multi-token local
  part. Lowercased, deduplicated, at least three characters, and only `[a-z0-9._-]`: a `+` or
  any other character a local part allows (`'`, `!`, ...) isn't a valid handle on the sites
  Username Search checks, so such a candidate is dropped.
- Username Search is the one place they appear. An email in the box, typed or arriving via `?q=`,
  gets a "Usernames from this email" chip row, and a click searches that candidate with the
  selected modules. An email `?q=` no longer auto-starts Maigret.
- Provider rules are only `+tag` (everyone) and Gmail dots. Separator variants are always on.

Putting the interception in Username Search fixes the palette and every existing "send to username
search" path at once, with no per-page wiring. The rules are exact for the address itself;
anything further (separator changes) is labelled a guess in the chip tooltip.

## Accepting

- `jdoe` shows up for `j.doe@outlook.com` too, as a separator guess rather than as the same
  mailbox. The tooltip says which.
- No candidates on the email-search, ioc_lookup or email-analyzer pages themselves. Getting there
  takes a palette pivot or pasting the address into Username Search.
- A future server-side consumer (such as an entity link graph) would need a Python port of the
  function.

## Rejected

- **A backend helper with an endpoint** - every consumer today is in the browser, and the graph
  that would need it server-side is not planned yet.
- **A per-provider rules table (Yahoo `-` and others)** - more correct for a few providers but
  needs upkeep, and a wrong rule turns a guess into a false "same mailbox".
- **Separator variants behind a "more variants" toggle** - they are a handful of chips, and a
  toggle is UI to explain for little gain.
- **Chip rows on email-search, ioc_lookup and email-analyzer results** - three integrations for
  what one interception in Username Search gives every entry point.
