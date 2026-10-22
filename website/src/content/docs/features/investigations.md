---
title: Investigations
description: Collect runs from several features, export them as one report, and see how their results connect.
sidebar:
  order: 200
---

An investigation is a named list of runs you already have in history: an IOC lookup, a username
search, an email search, a Reddit search. Group the runs that belong to one inquiry, write notes
on the whole investigation or on each run, export everything as a single HTML or PDF report, and
open the **Graph** tab to see how the results of different runs connect.

## Adding runs

Open a result from history in one of these features and click **Add to investigation**:

| Feature | What the run adds |
|---|---|
| IOC Lookup | The IOC, plus ASN (IP Geolocation), netblock (IP RDAP), hostnames (Shodan InternetDB), linked accounts (Gravatar) and breaches (Have I Been Pwned, LeakCheck) |
| Username Search | The username and every account found on a site |
| Email Search | mailcat: the username and the mailboxes found. user_scanner: the address and the services it is registered at |
| Reddit Search | The username and the subreddits it is most active in |

Pick an existing investigation from the menu or create one there. A run can be in several
investigations, and once in each. Runs of other features (Amass, Git Recon, Phone Search,
Steam Recon, Instagram Search, RU Business Check, Telegram Channels) can't be added yet. Domain Finder results
aren't saved to history, so they can't be added either.

An investigation points at the runs; it doesn't copy them. If you delete a run from its
feature's history, the investigation keeps the row, marked **Run deleted**, with its target and
your note. Its results are gone from the report and the graph. Deleting an investigation never
deletes the runs in it.

## Report

**HTML** and **PDF** on the investigation page export one report with:

- the investigation's name, creation date, notes and number of runs;
- how many runs come from each feature;
- each run in the order it was added, with your note and the same sections that feature's own
  export shows (for Reddit Search, the busiest subreddits and the 50 newest posts and comments);
- **Top connected entities**: the ten entities in the graph with the most links.

Report labels are in English. IOC Lookup sections follow the UI language, the same as its own
export.

## Graph

The **Graph** tab draws the entities from every run in the investigation and the links between
them. A value found by two runs is one node: if an email lookup and a username search both lead
to `jdoe`, the two runs meet there. Values are compared after normalization: case is ignored for
usernames, emails, domains and account URLs, a trailing dot is removed from domains, and `@` or
`u/` is removed from usernames. A bold border marks an entity that one of the runs was about.

- **Filter** by entity type with the chips above the graph. Each chip counts every entity of that
  type in the investigation, including ones the 300-entity limit left out.
- **Click** a node to see which runs found it, open its link (accounts) or look it up in another
  feature: IOC Lookup for an IP, domain, URL, email, hash, CVE or wallet, and Username, Email or
  Reddit Search for a username. An account offers the searches for its username. Links and
  lookups use the value as it was found, not the case-folded one used to match nodes.
- **Fit to view**, **Re-run layout** and **Export PNG** sit next to the filter.

The graph is built from the runs each time you open it, so it always matches what is in history.
It shows at most 300 entities. Past that, it keeps the most connected ones and says how many it
left out. Filter by type to see the rest.

There is one graph per investigation. To find links between two investigations, add their runs to
one investigation.
