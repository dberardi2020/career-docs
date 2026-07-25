# QA product map — career-docs

**The seasoned QA agent's memory.** Read this *first* so you act like someone who already knows the
product, not a first-timer fumbling through it — that is the difference between a cheap pass and one
that burns tokens rediscovering the obvious. Update it *last* with anything you learned. The
**fresh-eyes** agent must NOT read this file — its value is not knowing.

This doubles as the **regression baseline**: the checklist at the bottom is what must still work.
Each run, re-verify it and add any new surface. Point-in-time — update the "last verified" line.

**This is a QA lens, not a second product doc.** Canonical facts live in the repo's own docs — the
[`## Testing`](../README.md#testing) section and [`docs/technical/testing.md`](../docs/technical/testing.md)
for the layers and run story, [`docs/`](../docs/README.md) and the ADRs for the product and its
decisions. This file **links** there and holds only the QA *delta*: exact selectors, drive techniques,
gotchas, and the regression checklist. If something here is really a product fact, move it to the doc
that owns it and link — duplication drifts.

## Run the app

```bash
# unset the polluted env first (an installed .app leaks PYTHONHOME/PYTHONPATH and breaks the venv)
env -u PYTHONHOME -u PYTHONPATH .venv/bin/python qa/acceptance.py           # deterministic layer
env -u PYTHONHOME -u PYTHONPATH .venv/bin/python qa/acceptance.py --open     # + watch the viewer
env -u PYTHONHOME -u PYTHONPATH .venv/bin/python -m career_docs serve <profile> --port 8790 --no-open
```

Use `docs/assets/demo-profile.json` (Jane Smith) as the fixture — never a real resume.

## The viewer (`serve`) — surfaces & flows

- **Grid** is `<div id="grid">` — **empty in the served HTML; JavaScript builds the cards.** So HTTP
  checks see nothing; you must render in a real browser to test it (`--dump-dom` counts cards, or
  drive it live). A full page is 24 cards.
- **Header** is a two-column grid (`.hdr`, RP-0018): identity on the left (`h1`, `.statusline`,
  and `#hintBtn` in the left gutter on the dropdown row), controls on the right (`#pageMeta` + `.nav`,
  then the two filter rows `#palette` and `#axes`). `#hintBtn` ("What is this?") sits in the gutter
  aligned with `#axes` (the hero-shot layout, restored) — its `<p id="hint">` explainer still renders
  *below* the grid, shown on a first visit and hidden once dismissed. **Below 900px the grid collapses
  to one left-aligned column** — the control column is `auto` and cannot shrink, so two columns starve
  each other and the title breaks across three lines; there `#hintBtn` takes `order:1` so it drops
  *below* both filter rows instead of wedging between colour and the dropdowns. `.nav` is `flex-shrink:0`
  and `#pageMeta` is `min-width:0`, so the four `« ‹ Shuffle ›` controls never wrap — the count text
  yields instead (RP-0043).
- **Filter bar — two rows, one group (RP-0043, was one merged `#filters` bar in 171f20c).** Colour
  keeps its own row `#palette` (a `.swgroup`: label `Color` + 7 `.sw` swatches, `harbor ink moss clay
  plum slate crimson`, each `<button class="sw" title="moss">`), and the six dropdowns sit on the row
  directly below it, `#axes` (also `.palette` class; takes `grid-column:2` so nothing lands in the
  left gutter). They read as one group by adjacency and shared alignment — *not* by being concatenated
  into one wrapping container, which interleaves swatches and pills the moment it wraps. Both are
  right-aligned (left-aligned below 900px, where `#axes` drops to `grid-column:auto`). `.swgroup` is
  one flex item on purpose so a wrap cannot split the colour label from its swatches; `balanceWrap`
  runs on `#axes` only (the colour row is a single group). **Two resets, deliberately different
  weights:** the colour row ends with its own `.vchip` "Clear" (subtle — the same per-axis clear
  every dropdown popover carries, clears colour only), and `#axes` ends with the `.fpill.clearbtn`
  "Clear all" pill (the global reset). Both are always present, disabled when there is nothing to clear.
- **Axis dropdowns**: six `.fpill` pills —
  `Type Header Skills Promo Density Group` — each `<button class="fpill" data-axis="header">`
  carrying a `.ct` count badge when constrained and a `.caret` otherwise. Clicking one opens
  `#pop`, a **popover** listing that axis's values as `.val` buttons, each with a schematic
  `.thumb` icon. A popover is positioned, not laid out: **opening one must not change the
  header's height**. The detail dialog no longer carries filter bars — a filter belongs to the
  browse, not to one layout.
- **Every axis is a multi-select (RP-0033).** An axis holds a *set*: empty is unconstrained,
  several values are an OR, and axes combine with AND. A "hold" is just a selection of one.
  Selections ride on repeated query params (`?palette=moss&palette=plum`). Card chips are
  `<button class="chip" data-ax data-v>` and toggle the same filter. Two degenerate cases that
  must behave: selecting **every** value of an axis equals selecting none, and an **unknown**
  value is ignored rather than narrowing the browse to zero.
- **Filters FILTER the browse, server-side (RP-0033, changed 2026-07-23 — was an in-place overlay).**
  Clicking a swatch/chip sends the held axis as a query param to `/api/page`, which returns only
  matching layouts. So the browse **narrows**: hold `moss` → 1,440 layouts / 60 pages, `moss`+`charter`
  → 360 / 15; every card matches; **no 7×/4× redundancy** (the old overlay paged the full 10,080
  re-tinted). Holds **compose** and **persist across paging**; "Varied" (`data-p=""`/`data-t=""`)
  releases that axis. The header count **follows the filter** (see below).
- **Paging**: header shows `page N of <pages>` where `<pages>` tracks the *filtered* set (420
  unfiltered, 60 holding one palette, 15 holding palette+type); `«` first, `‹`/`›` prev/next, `[`/`]` keys.
- **Card** → `Open` → **detail modal**: buttons `Copy Name`, `Export PDF`, `★ Make this my resume`,
  `Close`, plus its own colour bar. `★ Make this my resume` → `POST /api/publish` → writes the
  deliverable (real PDF + HTML + MD) + `.career-docs.json` sidecar, archiving the previous.

## Driving it — hard-won technique

- **Get element coordinates from the DOM, do not pixel-hunt.** Swatches are 20px wide; a pixel
  guess lands in the gap and silently no-ops. Use `javascript_tool`:
  `[...document.querySelectorAll('#palette .sw')].map(e=>{const r=e.getBoundingClientRect();return{p:e.title,cx:Math.round(r.x+r.width/2),cy:Math.round(r.y+r.height/2)}})`
  then click those centres. (Screenshot coords are CSS px; `innerWidth` was 704, `dpr` 2.)
- **Responsive: always test a full window AND a half window — derive both at runtime, never a
  hardcoded width.** Do *not* trust the size the window launched at (it's arbitrary), and do *not*
  bake in a pixel number — a fixed "half screen" is wrong on any other display. Ask the page for its
  own screen and resize relative to it, so the check is identical on a laptop or a 5K monitor:
  `JSON.stringify({availW:screen.availWidth, availH:screen.availHeight})`, then
  - **Full window:** `resize_window` to `availW × availH`.
  - **Half window:** `resize_window` to `round(availW/2) × availH`.

  The header's one breakpoint is **900px** — a constant in the CSS (`@media (max-width:900px)`):
  ≥900 is two-column right-aligned, <900 is one left-aligned column. *Which* layout a full or half
  window lands in therefore depends on the machine, which is the whole reason to derive rather than
  guess. Also spot-check the breakpoint edges directly (**901 and 899**) since 900 is fixed in the
  code, not per-machine. At every width, assert from the DOM (not by eye): `#nav` on one line (all
  four buttons share a `y`), `#palette` above `#axes`, `#hintBtn` last in vertical order when
  single-column, and `document.documentElement.scrollWidth <= innerWidth` (no horizontal overflow).
  *(Hardcoding a width cost a redo on 2026-07-24 — a "half screen" eyeballed at 940 was really
  `availW/2 = 704` on that machine.)*
- **Verify publish by the filesystem, at the dir the server actually serves** — not the toast, not
  the folder you *think* you served. Publish is server-side + a real ~2s PDF render.
- **Turn on `read_network_requests` BEFORE the action** you want to capture — tracking starts on
  first call, so a click made earlier won't be in it.

## Gotchas (read before diagnosing a "bug")

- **Stale-server / wrong-dir trap.** A `serve` from a previous session can still hold the port; your
  new `serve` then **fails silently on the port conflict and you drive the OLD server**, which
  publishes to *its* cwd. Symptom: publish returns 200 but "nothing is written" — because you are
  checking the wrong folder. Before trusting a publish check: `lsof -iTCP:8790 -sTCP:LISTEN` and
  `lsof -a -p <pid> -d cwd` to confirm which server and dir. Kill stale servers or use a fresh port.
  *(This one cost a false bug report on 2026-07-23 — do not repeat it.)*
- The starter/demo resume lints with an ERROR (placeholder bullet has no figure) — that is correct
  behaviour, not a failure.

## Regression checklist (the PIT)

Re-verify each; expected result in parens. Add new rows as surface grows.

| # | Behaviour | Expected | Last verified |
|---|---|---|---|
| 1 | Grid renders in a real browser | 24 cards from an empty `#grid` | 2026-07-23 ✅ |
| 2 | Colour filter | click `moss` → header "1,440 of 10,080 layouts", "page 1 of 60", every card moss | 2026-07-23 ✅ (driven live) |
| 3 | Filter persists + no redundancy across paging | page 2 still all moss, different layouts (not the same design re-tinted) | 2026-07-23 ✅ (driven live) |
| 4 | Paging | `›` → "page 2 of 420" unfiltered, new layouts | 2026-07-23 ✅ |
| 5 | Detail modal | full-page render + publish controls | 2026-07-23 ✅ |
| 6 | Viewer publish | deliverable + real PDF + sidecar records the picked layout + archive-on-overwrite | 2026-07-23 ✅ |
| 7 | Typeface filter + compose | `Type ▾ charter` → all cards that face; `moss`+`charter` → "360 of 10,080 layouts", page 1 of 15; clear → back to 10,080/420 | 2026-07-23 ✅ (driven live) |
| 8 | Counts follow the filter (RP-0035) | header total & page count recompute per hold; `/api/page` returns live `total` | 2026-07-23 ✅ (driven live + acceptance) |
| 9 | Header holds its shape | with several axes filtered the `« ‹ Shuffle ›` nav stays on row 1 (never wraps); colour (`#palette`) and dropdowns (`#axes`) are two stacked rows reading as one group, not one merged bar; below 900px both collapse to one left-aligned column | 2026-07-24 ✅ (RP-0043; measured live at 1400 / 950 / 700 / 500px — nav one line at every width, rows stacked and aligned, `#axes` grid-column auto below 900px) |
| 10 | Explainer collapses and stays collapsed (RP-0018) | `#hintBtn` toggles `#hint` and flips its label between "What is this?" and "Hide"; the choice persists across a reload via `localStorage["career-docs:hint-hidden"]` | 2026-07-23 ✅ (driven live) |
| 11 | **Multi-select is an OR** (RP-0033) | two densities → total = 2/3 of the single-density set; the `Density` pill shows a `2` badge; both values appear in the grid | 2026-07-23 ✅ (driven live + acceptance) |
| 12 | **A dropdown must not move the header** | opening any `#axes` pill leaves the header height unchanged — a popover is positioned, not laid out. Measured delta `0px` | 2026-07-24 ✅ (re-measured live after the RP-0043 two-row restore: header 161px, delta 0px) |
| 13 | **Card chip filters** | click a card's `clay` chip → "1,440 of 10,080 layouts", the chip goes `.on`, `Clear all` enables | 2026-07-23 ✅ (driven live) |
| 14 | **Clear all resets everything** | one click → 10,080, no `.on` chip or swatch anywhere, the button re-disables, header returns to its resting height | 2026-07-23 ✅ (driven live) |
| 15 | **Degenerate filters behave** | selecting *every* value of an axis == no filter (10,080); an unknown value is ignored rather than yielding "0 layouts" | 2026-07-23 ✅ (acceptance) |
| 16 | **Full window AND half window both hold** (derive both, never hardcode) | resize to `availW×availH` (full) and `round(availW/2)×availH` (half), plus the breakpoint edges 901/899. At each: `#nav` on one line, `#palette` above `#axes`, `#hintBtn` last in vertical order when single-column (`order:1`), no horizontal overflow (`scrollWidth<=innerWidth`). Do **not** trust the launch size; do **not** bake in a pixel width | 2026-07-24 ✅ (RP-0043 follow-up; this run availW=1408 → full 1408px two-column, half 704px single-column 2-card grid; both sides of the breakpoint exercised at 940 (two-col) and 899 (one-col); all held, no overflow) |

## Teardown (always — a QA cleans up)

Kill any `serve` you started (`kill <pid>`), remove temp workspaces (`rm -rf`), close the browser
tab you opened. Leave the machine as you found it.
