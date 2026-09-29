---
title: Sanctions Search
description: Search a locally cached mirror of the OFAC SDN sanctions list by name.
sidebar:
  order: 190
---

Searches a locally cached mirror of the US Treasury OFAC SDN (Specially Designated Nationals)
list by free-text person, organization, vessel, or aircraft name — a general-purpose sanctions
name check, distinct from [RU Business Check](/corvid/features/ru-business-check/)'s narrower,
ИНН-exact OFAC lookup (which only matches Russian tax IDs, not names).

The list is downloaded from [OpenSanctions](https://www.opensanctions.org/)' cleaned CSV mirror
of the SDN dataset (CC-BY 4.0), refreshed every two days, and matched locally — the searched name
is never sent to a third party. Matching is exact and substring comparison against each entity's
name and known aliases, ranked with exact matches first; there is no fuzzy/phonetic matching, so
a misspelled name may not surface a real match, and a substring match on a common name is expected
and should be reviewed rather than treated as a confirmed hit.

Results are ephemeral, like [Dork Runner](/corvid/features/dork-runner/) — no history is
persisted.
