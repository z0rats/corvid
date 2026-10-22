---
title: Username Search
description: Find accounts registered to a username across hundreds of sites.
sidebar:
  order: 50
---

Searches for a username across a large list of sites. The form shows a chip per source; select
any combination and each selected one runs as its own scan, with its own entry in history. Three
engines back the same result view:

- **[Maigret](https://github.com/soxoj/maigret)** — runs in-process, with true per-site progress
  streamed live as each site is checked. Configurable timeout, concurrency, and how many
  top-ranked sites to check, plus an optional proxy. Its site database updates independently of
  the app, tracked in settings.
- **[Social Analyzer](https://github.com/qeeqbox/social-analyzer)** — runs as a subprocess of its
  own CLI rather than in-process (its installed package can't be imported directly), so progress
  reporting is coarser: a "started" event, then one terminal result. Configurable timeout and
  top-site count; a hard wall-clock watchdog force-kills a run after 30 minutes even with no
  client still watching, since both settings can be configured unbounded.
- **Threat Actor Usernames** — a single lookup against the public
  [threatactorusernames.com](https://threatactorusernames.com) index of usernames scraped from
  cybercrime and threat-actor forums. A hit names the *forum* the handle was seen on rather than a
  profile URL, and there's no per-site progress — just a "started" event and one result. Requires
  no key and has no settings.

Maigret and Social Analyzer expose their installed version and whether a newer release is available
under their respective settings; installing an update still requires a container rebuild, since both are
pinned in `requirements.txt` at image-build time.

If a username search turns up an Instagram profile, see
[Instagram Search](/corvid/features/instagram-search/) for profile metadata plus follower/followee/post
scans.

## Infostealer exposure check

The fourth chip, **Hudson Rock**, isn't a scan engine: it's a separate, quick,
keyless lookup against Hudson Rock's free infostealer-exposure API. The result is a status chip
above the found-sites list — "No infostealer exposure" or "N infostealer infection(s) found" — with
Hudson Rock's attribution. It isn't saved to history, and a username match is a lead rather than
proof the account belongs to the person you're researching.

## Suggested variants

While you type, the search form suggests other handles the same person might use — separator
changes (`john.smith` / `john_smith`), a dropped or swapped trailing year, first/last-name
patterns (`jsmith`, `smithj`), common nicknames (`john` → `johny`), common number suffixes
(`john` → `john1`, `john123`), single-character leetspeak, and a few prefixes/suffixes. If you
paste an email address, its local part is used. Clicking a suggestion puts it in the box; it
doesn't start a scan. Suggestions are generated in the browser with no lookups, are guesses rather
than findings, and a hit under a variant still needs manual verification — different people share
handles.

## Usernames from an email

An email address in the box gets a separate row, **Usernames from this email**: the mailbox name
as-is, the same without a `+tag` (`j.doe+news@…` → `j.doe`), the dotless form for Gmail and
Googlemail only (Gmail ignores dots, so `j.doe@gmail.com` and `jdoe@gmail.com` are one mailbox),
and separator changes of a `first.last` name (`j_doe`, `jdoe`, `j-doe`). Candidates shorter than
three characters, or with characters other than letters, digits, `.`, `_` and `-`, are dropped. Unlike the variants above, clicking one of these starts a search
with the selected modules straight away, and the email stays in the box so you can try the next.

An email sent here from elsewhere (for example the command palette's `j.doe@gmail.com username`)
lands in the box the same way and doesn't start a scan on its own, since a whole address is rarely
anyone's username.

## Patterns

When you know part of a handle's structure, write it as a pattern instead — any `[` in the box
switches it to pattern mode:

| Syntax | Meaning | Example → expands to |
| --- | --- | --- |
| `[abc]` | one character from the set | `john[abc]` → `johna`, `johnb`, `johnc` |
| `[a-z]`, `[0-9]` | a range; put `-` first or last for a literal dash | `a[_.-]b` → `a_b`, `a.b`, `a-b` |
| `[set]{n}` | exactly *n* characters | `c[0-1]{2}` → `c00`, `c01`, `c10`, `c11` |
| `[set]{n-m}` | *n* to *m* characters (`{0-2}` makes it optional) | `user[0-9]{0-1}` → `user`, `user0`, … `user9` |
| `[set]{n;m}` | *n* or *m* characters (can mix: `{0-1;3}`) | `u[a]{1;3}` → `ua`, `uaaa` |
| `\[` `\]` `\\` | a literal bracket or backslash | `hello\[w\]` → `hello[w]` |

The form lists up to 100 of the resulting handles (and how many there are in total); clicking one
puts it in the box so you can search it. A pattern is never searched as a whole — one search
already checks hundreds of sites — and one that matches more than 10,000 handles is refused as too
broad. Characters are kept as typed, so `[jJ]ohn` yields both cases.

## Pivot suggestions after a scan

When a scan finishes (also on a past run's detail page), a "Pivot suggestions" block lists:

- **Other usernames** found on the profile pages Maigret parsed. A handle the page itself named
  is *reported*; a profile link the owner typed in (for example an `x.com/…` or `linkedin.com/in/…`
  URL) is resolved to the account it points at, and its tooltip says which site. Links to site
  pages (`github.com/settings`), deep paths, personal websites and URL shorteners are ignored.
  Clicking a handle starts a Maigret search for it.
- **Platform account IDs** (a VK or Steam ID, say). These aren't usernames, so they can't start a
  search — look them up on their own platform.
- **Display names**, and **handle guesses from each name** (`John Smith` → `johnsmith`,
  `jsmith`, …) using the same rules as the suggested variants above.
- **Email addresses the profiles published** in their own email fields. Role mailboxes
  (`noreply@`), placeholder domains and GitHub's relay addresses are dropped. Clicking one opens it
  in the [IOC lookup](/corvid/features/ioc-tools/). Only runs made after this was added carry them.
- **Possible email addresses** for the searched handle at common providers, opening the same
  lookup, plus a button to [Email Search](/corvid/features/email-search/) to check which mail
  providers have the username.

Only Maigret-sourced runs carry the first four, and only for sites whose page it can parse. All of
it is hypotheses: the same handle or name is often a different person, so verify before
attributing. Nothing here is fetched beyond what the scan already collected.

## Confirming a pivot, and how sure to be

A handle taken from a profile link already names its site, so it gets a **Check on {site}** button
next to the usual click-to-search: one request to that one site instead of a full scan. It runs as
an ordinary run in your history (labelled **Maigret site check**), limited to 5 per minute (a full
scan stays at 3 per minute); if you hit the limit the panel says to wait a minute. A site that
blocked the check or rejected the handle is shown as "could not check", in the panel and in
history alike — never as "not found". Nothing follows a chain on its own — every step
is a click.

Both kinds of follow-up remember the run they came from. History shows a **From run** column and
the run's page a "Followed from run #N" line (plain text if that run was deleted since). Each
profile such a run finds is rated against what the source run already knew:

| Rating | Meaning |
| --- | --- |
| Confirmed | This exact account (site and handle) was linked from a profile of the source run |
| Likely | The profile repeats a name, email, personal website or linked account known from that run |
| Candidate | Nothing to compare it with, or nothing matched |
| Conflicting | The profile names a different person than the source run's profiles do |

Results are sorted best first. This is triage, not a verdict: a name that just restates the handle
is ignored, a location is never used, nothing is hidden, and it says little for sites that show no
profile details. Plain scans from the form carry no rating. Only Maigret-sourced runs take part.

## Report export

Maigret-sourced scans can export using Maigret's own report writers (see
[Reports & Exports](/corvid/architecture/reports/)). Social-analyzer-sourced scans don't support
export.
