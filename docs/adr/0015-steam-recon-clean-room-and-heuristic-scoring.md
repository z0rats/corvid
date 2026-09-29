# Steam Recon is a clean-room reimplementation with a transparent heuristic, not a ported ML model

Steam Recon (geolocation-by-social-graph, close-friends ranking, CS2 cheater-probability
report) reproduces the technique described in [SteamReveal](https://github.com/Berchez/SteamReveal)'s
README. Two decisions were made before writing any code: not to reuse SteamReveal's code, and
not to reproduce its ML-based cheater classifier.

## Clean-room, not a port

SteamReveal's repository carries no license (`license: null` via the GitHub API) - under
default copyright, that means all rights reserved, and its code cannot legally be copied into
this AGPL-3.0 project. Its README, technique description, and public Steam Web API documentation
were used as the specification; no SteamReveal source file was read or referenced while writing
this module's code. This module's file layout, naming, and Python idioms follow this codebase's
own existing scan-style features (`git_recon`, `email_search`), not SteamReveal's Next.js/
TypeScript structure - there was nothing to diverge from, since nothing was copied to begin with.

## Heuristic scoring instead of SteamReveal's ML classifier

SteamReveal's cheater-probability feature is a trained ML model (a separate Flask backend, per
its README) analyzing profile-comment sentiment, ban proximity, account investment, and CS2
stats. Reproducing it was considered and rejected:

- **No training data or trained weights are available.** The model itself, and whatever labeled
  dataset it was trained on, are SteamReveal's own artifacts - reimplementing "a similar model"
  from scratch would mean inventing training data (fabricated ban/cheat correlations) or trying
  to reverse-engineer weights from observed behavior, neither of which produces something
  trustworthy enough to base an OSINT judgment on.
- **A second backend service is exactly the shape this project avoids.** SteamReveal's own
  README describes cheater probability as needing a separate Flask prediction service; this
  project's `docs/architecture/steam-recon.md` and the broader minimize-dependencies convention
  (`CLAUDE.md`) both push against adding infrastructure for one feature's scoring step.
- **An opaque score is a worse fit for an OSINT tool than an explainable one.** A single ML
  probability gives an analyst nothing to check it against; a security-analyst tool should let
  its user see *why* a number came out the way it did, not just the number.

Chosen instead: a hand-weighted logistic combination of five independently-explainable signals
(`service/steam_cheater_scoring_service.py` - own bans, friend ban density, account investment,
CS2 stat outliers, accusatory-comment ratio), each reported with its own value, weight and
contribution, plus a `coverage` field showing how much of the picture was actually available.
This trades whatever accuracy SteamReveal's trained model might have for something this project
can build, test, and explain without external infrastructure or fabricated training data. The
tradeoff is explicit: this heuristic will not match SteamReveal's model's accuracy, and isn't
claimed to - see the in-app disclaimer and `docs/architecture/steam-recon.md`'s signal table.

## Platform-ban signal (Faceit/GamersClub) dropped, not reproduced

SteamReveal boosts its probability when the target has a ban on Faceit or GamersClub anti-cheat.
GamersClub has no public API found during phase-0 scoping, so that half was never viable
keylessly. Faceit's Data API v4 does exist and would have added the corresponding half of the
signal, but was explicitly descoped by the project owner rather than half-implemented - a
platform-ban signal covering only one of the two source platforms was judged not worth the
extra optional API key and integration surface for this iteration. This can be revisited as a
later addition if wanted; nothing in the current signal set assumes its absence.
