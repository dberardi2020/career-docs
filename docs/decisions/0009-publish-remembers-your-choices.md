# 0009 — Publish remembers your choices in a sidecar

**Status:** Accepted · 2026-07-23

## Context

The common loop is not "pick a layout once" — it is edit the content, re-publish, edit again.
But `publish` took the layout as a `--theme` argument that defaulted to `default`, and recorded
nothing. So a bare re-publish after a content edit **silently switched the layout** back to the
default, discarding whatever the user had chosen in the viewer. The chosen layout lived only in
the user's memory. Separately, not everyone wants all three formats, but `publish` always wrote
`.pdf` + `.html` + `.md` with no way to narrow the set — and any per-user "which formats" choice
would have the same forgetting problem.

Both are the same gap: two publish *choices* — which layout, which formats — with nowhere to
persist between runs.

## Decision

**Publish records the chosen layout and formats in a hidden sidecar,
`.career-docs.json`, beside the deliverable. A bare re-publish reuses them; an explicit
`--theme` or `--formats` overrides and re-records.**

```json
{ "layout": "ink-charter-masthead-inline-stacked-normal-grouped", "formats": ["pdf"] }
```

Rejected alternatives: an HTML comment in the deliverable (lost the moment the file is deleted —
the choice must outlive the generated files); a key inside `resume.json` (the tool must not write
the hand-edited source of truth); a global `~/.config` file (it would not cross the file-sync that
carries the workspace between machines, so two machines would disagree).

## Rationale

- **Durable.** The sidecar outlives deleting every deliverable; only deleting the sidecar itself —
  an explicit reset — clears the choice.
- **Folder-local, so it composes.** The record sits beside the deliverable it describes, so each
  folder remembers its own — the main resume, and later each tailored application — with no
  path-keyed global state.
- **Same pattern as the name.** `existing_stem` already reuses the deliverable's *name*; this
  reuses its *layout* and *formats*. "Complete deliverable" now means the recorded formats are
  present, so a PDF-only deliverable still matches its name.

## Consequences

- Bare `publish` after a content edit keeps the design; switching layout or formats is explicit.
- The folder gains one hidden file. It is tool state, not a document, and never the answer to
  "which file do I send?".
- The schema is intentionally room-to-grow: a future set of *named* loadouts (RP-0004) extends
  this record rather than replacing it. Surfacing format choice in the viewer is RP-0030.
- A deliverable published before this exists has no sidecar; the tool falls back to the defaults.
