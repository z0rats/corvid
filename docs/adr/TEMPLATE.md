# <The decision, stated as a short present-tense sentence>

<Context: what forced a choice, in a paragraph or two. Facts the decision rests on - that a
channel exists, that a source behaves a certain way - name how they were checked.>

## Decision

<What was decided, in enough detail to apply it. Present tense, current state only.>

<Because: the reasoning a reader needs to accept it. Inline here, not a separate heading.>

## Accepting

<What this choice costs - the downside knowingly taken on. Omit the section if there is none.>

## Revisit

<Optional. The condition or occasion that would settle a provisional decision, e.g. "if a second
consumer needs live push". Its presence marks the decision as provisional: `grep -l "^## Revisit"
docs/adr/*.md` lists every one.>

## Rejected

- **<Alternative>** - <why it lost>. One bullet per alternative someone could plausibly propose
  again; a rejection without its reason gets re-proposed.

<!-- A flipped decision is never rewritten in place: the old ADR keeps its number and gets
`Superseded by NNNN-<slug>.md` as its first line under the title, and the new ADR lists the old
pick under `## Rejected` with the reason it lost this time. -->
