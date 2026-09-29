---
title: Steam Recon
description: Steam profile lookup, friends-graph geolocation, close-friends ranking, and a CS2 cheater-probability report.
sidebar:
  order: 110
---

OSINT analysis of a Steam profile, targeted by a SteamID64, SteamID3 (`[U:1:N]`), SteamID2
(`STEAM_X:Y:Z`), a `steamcommunity.com/profiles/…` or `/id/…` URL, or a bare vanity name.

Needs a free **Steam Web API key**, configured under Settings → API Keys. Get one at
`steamcommunity.com/dev/apikey`; the Steam account must not be limited (at least $5 spent).
Steam allows roughly 100,000 requests per day per key.

## Profile tab

A quick, single-request lookup: profile summary, ban record (VAC, game, community, trade),
Steam level, game count, self-declared location, and deep-links to external lookups
(steamid.io, SteamDB, csstats.gg, Leetify). A private profile still returns what Steam exposes
publicly; fields it hides (game count, level, account creation date) show as unknown.

## New Scan tab

Collects the target's friends graph and analyzes it:

- **Close friends** — ranks the target's public friends by mutual-connection weight
  (`closeness(i) = |friends(i) ∩ friends(target)|`), not just friends-list order. The friend
  cap (default 200, up to 500) is applied to the oldest connections first, on the assumption an
  older friendship is more likely a genuinely close one; each kept candidate's own friend list
  is then fetched to compute its mutual-connection weight against the target's full friend set.
- **Geolocation hypothesis** — a weighted vote of connected friends' self-declared locations,
  aggregated hierarchically (country → region → city), with a high/medium/low confidence rating
  based on the leading candidate's vote share, voter count, and location coverage. This is a
  hypothesis, not a fact, and is shown next to the target's own self-declared location (if
  public) for comparison.
- **Friends graph** — a radial diagram (self-drawn SVG, no charting library) of the target and
  its top close friends, sized and connected by mutual-connection weight.
- **CS2 cheater-probability report** (optional, on by default) — a transparent, explainable
  heuristic across five signals: the target's own VAC/game ban (weighted by recency),
  ban density among connected friends, low account investment (age/level/game count), CS2 stat
  outliers (headshot ratio, accuracy, K/D), and an accusatory-comment ratio from the target's
  public profile comments. Every signal shows its own value, weight and contribution; a signal
  with no usable data contributes nothing rather than being scored as innocent. This is a
  heuristic estimate, not a verdict — see the in-app disclaimer.

A scan streams live progress and can be cancelled mid-run; past scans are kept under the
History tab. Unlike Profile-tab lookups, a scan costs roughly one Steam Web API call per
analyzed friend plus a handful more — the form shows an estimated call count before starting.

Deep-dive (algorithms, config values, confidence thresholds, live-verification notes):
`docs/architecture/steam-recon.md`.
