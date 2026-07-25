# Platforms and status

An honest ledger: what works, what is verified, what is experimental, and what is not built.
Kept blunt on purpose — the README leads with what the tool does, and this is where the
qualifications live.

*Current as of 2026-07-22.*

## Verified

| Platform | State |
|---|---|
| **macOS** | Verified end to end — developed here. CI runs Python 3.11 and 3.13. |
| **Linux** | Verified in CI (Ubuntu, Python 3.11 and 3.13), including PDF export against Chromium. |
| **Windows** | **Unverified**, and therefore off the platform badge for now. Nothing is known to be platform-specific — `pdf.py` has Windows browser paths, and everything else is stdlib — but no one has run it. Verifying it and restoring the badge is RP-0027. |

Python 3.11 is the floor (`pyproject.toml`); the code uses `X | Y` unions and `:=`.

## What works

| Area | State |
|---|---|
| The 7-axis, 10,080-spec space | Works. Every name round-trips, asserted across the whole space. |
| Rendering | Works. `render(profile, spec)` is pure; every spec in the space renders. |
| Layout + content linter | Works. 20 rules, three severities. Reports only. |
| The viewer | Works, in both deliveries — static folder and served. Served adds paging, shuffle, colour + typeface holds that **filter** the browse to the held subset, and publish-in-place. |
| Publish (PDF / HTML / Markdown) | Works. PDF needs a browser; the other two do not. |
| `init` workspace scaffold | Works, and ships the `career-resume-update` + `career-layouts-browse` agent skills. |
| Tests + CI | 208 tests, plus an on-demand acceptance harness (`qa/`). Green on macOS + Linux × Python 3.11/3.13. |

## Experimental

**`work[].stints`** and the **`grouping`** axis — per-title bullets within one employer, so a
promotion can show *which* work was done at which level.

It ships and is tested, but it is a local schema extension JSON Resume has no field for, and
**no real document has exercised it**: the author's own resume was migrated onto it and then
migrated back, because a flat bullet list plus a `note` said the same thing with less
machinery. That is evidence about the feature, not just caution.

Prefer flat `highlights` plus a `note` unless per-title bullets are genuinely needed. Do not
build further features on it. See RP-0024.

## Not built

In rough order of how much they matter:

| | |
|---|---|
| **Import an existing resume** (RP-0001) | PDF/DOCX → profile. The adoption cliff for this whole category — today you transcribe once before anything works. |
| **Axis grouping** | Every axis filters and a card's chips filter on click (RP-0033, shipped). Still missing: clustering the grid *by* an axis, so a page reads as "these are the mastheads" rather than a mixed spread. |
| **The inspector** | A live, read-only view of the profile as it is edited, showing what changed. The answer to "watching an agent rewrite my career history is unnerving". |
| **Provenance** (RP-0007) | Per claim: human-asserted fact, or model-generated prose. The necessary counterweight to a linter that asks for numbers. |
| **Cover letters and applications** (RP-0009) | Same data model plus a job posting. Folders are scaffolded and empty. |
| **Remix / loadouts / merge** (RP-0003/4/22) | All the same move — constrain some axes, browse the rest. Waiting on the axis-control UI. |
| **Working without a local install** (RP-0023) | Hosted, WASM, or a zero-install agent path. Undecided, and the options differ on where the profile lives. |

## Known limitations

- **One HTML skeleton.** Every layout renders from the same structure, so variety comes from
  colour, type and the treatment of details. Two profiles in different palettes look more
  alike than 10,080 suggests.
- **No pagination control.** Content flows; you cannot force a break or target one page.
- **PDF requires a local browser.** The single external dependency, and the one thing that
  makes a hosted version non-trivial.
- **Markdown output is a flattening.** It preserves content, not layout — deliberately, since
  it exists to diff and to paste.
- **`resume.json` is validated, not schema-checked.** Structural and date validation is
  hand-rolled; the profile is not run against the published JSON Resume schema.

## Non-goals

- A web form or a template gallery. Wrong shape; see [`overview.md`](overview.md).
- Being another resume generator. That category is mature and mostly abandoned.
- The [JSON Resume registry](https://registry.jsonresume.org). Publishing there requires a
  **public gist**, an OAuth scope that reads and writes **all** your gists, and copies the
  resume into a third-party database.
