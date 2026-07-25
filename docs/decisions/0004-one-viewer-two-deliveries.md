# 0004 — One viewer, parameterised by delivery

**Status:** Accepted · 2026-07-21 · amended 2026-07-24 (RP-0038)

## Context

There were two implementations of the same page. `catalogue.py` built a static grid of scaled
iframe previews with axis chips; `explore/ui.py` served a grid of scaled iframe previews with
axis chips. They shared no code — the same CSS variables, the same card structure and the same
scaling logic existed twice — and had already begun to drift.

## Decision

**One viewer.** `viewer.page(specs, resume, *, preview, exportable)` is the only UI, and the
two deliveries differ in exactly two switches:

- **where a preview comes from** — the baked `markups`/`css` tables reassembled in the browser
  (`preview="embed"`), or a `/preview/<name>` route (`preview="route"`);
- **whether the page can act** — a served page can export and publish; a static one cannot,
  so those controls are absent rather than present and broken.

An unknown `preview` raises rather than rendering a page that half works.

## Rationale

Duplicated UI drifts, always, and the drift is invisible until someone compares screenshots.
Both deliveries are genuinely wanted — a static folder can be committed, linked or sent, and a
`file://` path outlives a localhost URL — but that is a difference in *delivery*, not in
product.

## Consequences

- `explore/` was deleted; `catalogue.py` fell to 37 lines because the viewer does the work.
- **A test normalises the two outputs and asserts equality**, so a third difference cannot
  appear without someone deciding to add it.
- Preview HTML is always a **live render** — the same function that publishes — so nothing on
  screen can drift from what is produced. This is also why previews are HTML rather than
  pre-rendered images: an earlier version generated a PDF per variant at roughly a second
  each, which capped how much of the space was worth looking at.
- The viewer's JavaScript is asserted as a string and never executed. There is no browser in
  the test loop.

## Amendment — 2026-07-24

The guardrail above was bypassed, exactly once and exactly as predicted.

RP-0038 added a **third** delivery, `preview="embed"`, for the hosted demo: no server, the
whole space enumerated and filtered client-side, every preview rebuilt from tables baked at
build time. The equality test was not extended to it, so for the life of that change the mode
destined for the public internet was the only one nothing verified — and `demo.py` had no test
of any kind, including for the bake invariant it rests on.

That cost something concrete. The kit's `button{display:inline-flex}` silently beat the UA's
`[hidden]{display:none}`, and the resulting bug — a static catalogue offering an *Export PDF*
and a *Make this my resume* with no backend behind either — was visible in exactly one
delivery and caught by eye, not by CI.

**Back to two.** `preview="file"` is deleted. It was the weakest delivery — a fixed 21-layout
spread with no filters and no paging, because a folder on disk had no backend to ask — and
`embed` dominates it: also static, also no backend, but browsing and filtering all 10,080.
`catalogue` now emits an `embed` index and keeps what was actually unique to it, the per-spec
renders and `options.json` written beside that index.

**Consequences of the amendment**

- Two deliveries again, and both filter. There is no lesser mode for a bug to hide in.
- The equality test compares `embed` against `route`, normalising the baked tables (a data
  payload, not a difference in the page).
- The **bake invariant is now tested**: all 10,080 specs, asserting the reassembly equals
  `compose.render` byte for byte — up to the newline `render` writes after `</html>`, which is
  outside the root element. It costs ~0.3s, so it checks the space rather than a sample.
- `bake`/`rebuild` moved from `demo.py` to `viewer.py`. Both static outputs need them, and
  `catalogue` importing `demo` would have had the dependency backwards.
- `demo.py` has build-level tests: the site is emitted, is self-contained (no CDN, no remote
  fonts, no external scripts), drops stale pages, and runs the same delivery as `catalogue`.
- Cost accepted: the catalogue index went from 56K to 1.6M (41K gzipped) because it now
  carries the tables for the whole space. Worth it — a static folder that browses 10,080
  layouts beats one that shows 21.
