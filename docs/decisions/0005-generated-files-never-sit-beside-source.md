# 0005 — Generated files never sit beside source

**Status:** Accepted · 2026-07-21

## Context

Renders pile up: every layout, in HTML and PDF, every time someone looks. Written beside the
profile they bury the one authored file under hundreds of derived ones — and a resume folder
is usually file-synced, so it churns megabytes that a single command reproduces.

The counter-argument was made and briefly won: a catalogue exists *to be looked at*, so
perhaps it should live where the resume does and stay findable.

## Decision

**Everything generated goes to `${XDG_CACHE_HOME:-~/.cache}/career-docs/<workspace>/`.**
The single exception is `publish`, which writes one canonical deliverable beside the profile.

## Rationale

The findability argument is real but the remedy was wrong: findability comes from **printing
the `file://` link**, not from the folder's location. Once that is said out loud, the cost of
writing into a synced workspace buys nothing.

A resume folder should answer one question instantly — *which file do I send?* Exactly one
set of generated files belongs there, and only because it is the answer.

## Consequences

- `catalogue` writes to the cache and prints a link. Deleting the cache is always safe;
  rebuilding is instant and deterministic.
- `publish` overwrites one fixed trio in place rather than accumulating layout-suffixed
  variants.
- **Publishing reuses a deliverable name already present in the folder.** Deriving one instead
  produced `Smith_Resume.*` beside an existing `Resume_Smith.*` — which does not replace a
  deliverable, it duplicates it, leaving two resumes and one of them stale.
- The workspace `CLAUDE.md` states the rule, so an agent working there inherits it.
