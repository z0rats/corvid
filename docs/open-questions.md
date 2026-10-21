# Open questions

Product questions that are not settled yet, and the process that settles them. A settled question
worth keeping becomes an ADR (`docs/adr/TEMPLATE.md`) and leaves this file.

## Before a feature

For a change that alters what the user sees or what is stored (schema, persisted settings, files
under `data/`):

1. **Open questions.** The owner writes a short list of what is undecided. The agent writes its own
   list independently, without reading the owner's first, then merges both into one and names
   anything it dropped and why.
2. **Options.** Every question, even a trivial one, gets candidates and the criterion that tells
   them apart.
3. **Verdicts.** One pick per question, with its reason, its cost and the rejected candidates. A pick
   that flips reopens the decisions that rested on it.
4. **Then code.** Verdicts with a real alternative become ADRs. A question that comes up while
   coding goes through steps 2-3 first, not straight into the code; one that can't be settled now
   goes under Open below.

## Open

Entry format: `- **OPEN-<n>. <question>.** <what is known, options so far>`. IDs are never reused.

None right now.
