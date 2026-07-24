# Tickets

The backlog. Board-first: a lightweight tracker until a real one is warranted. IDs are `RP-NNNN`, uppercase, never reused.

**What is *not* here:** the steps to *take the repo public* — secrets scan, private-content sweep, the flip. Those are a **pre-flight checklist run once when the project is ready**, kept as a separate release runbook, not backlog. This board tracks *building the product*.

Rows are pointers; anything needing more than a sentence has a block in **Details**, below the board.

## In progress

*(none)*

## On deck

The committed next few, in intended order.

| ID | Pri | Type | Title |
|---|---|---|---|
| [RP-0043](#rp-0043) | P1 | Bug | Filter bar regressions — one merged row, and the nav wraps |
| [RP-0038](#rp-0038) | P1 | Feature | A hosted GitHub Pages demo — fixture data, click-around, no backend |
| [RP-0032](#rp-0032) | P1 | Feature | Lead with a small, diverse set — the full space overwhelms |

## Blocked

*(none)*

## Backlog

| ID | Pri | Type | Title |
|---|---|---|---|
| [RP-0001](#rp-0001) | P1 | Feature | Import an existing resume (PDF/DOCX → `resume.json`) |
| [RP-0007](#rp-0007) | P1 | Feature | Provenance model — asserted fact vs. model-generated prose |
| [RP-0018](#rp-0018) | P1 | Chore | UI/UX pass on the viewer |
| [RP-0025](#rp-0025) | P1 | Feature | `import` as a skill, not a parser |
| [RP-0039](#rp-0039) | P1 | Feature | Publish a subset of skills without deleting from the profile |
| [RP-0041](#rp-0041) | P1 | Feature | Bundle deterministic fonts — the typeface axis resolves differently per machine |
| [RP-0042](#rp-0042) | P2 | Feature | Group the grid by an axis |
| [RP-0003](#rp-0003) | P2 | Feature | Remix — pin a layout and vary one axis at a time |
| [RP-0004](#rp-0004) | P2 | Feature | Global style locks + loadouts |
| [RP-0008](#rp-0008) | P2 | Feature | Explain what an ATS actually is, evidence-first |
| [RP-0009](#rp-0009) | P2 | Feature | Cover letters, from the same data model |
| [RP-0016](#rp-0016) | P2 | Chore | Keep the hosting path open |
| [RP-0023](#rp-0023) | P2 | Feature | Work without a local download, install or clone |
| [RP-0027](#rp-0027) | P2 | Chore | Verify on Windows, then restore the badge |
| [RP-0028](#rp-0028) | P2 | Feature | HEX / custom palettes — an open palette axis |
| [RP-0030](#rp-0030) | P2 | Feature | Surface format choice in the viewer |
| [RP-0034](#rp-0034) | P2 | Feature | Named styles / archetypes as browse entry points |
| [RP-0005](#rp-0005) | P3 | Feature | A content design space, alongside the style space |
| [RP-0006](#rp-0006) | P3 | Feature | Drag-and-drop builder for sections and variants |
| [RP-0013](#rp-0013) | P3 | Feature | Lint variants, not the master profile |
| [RP-0014](#rp-0014) | P3 | Chore | `work[].promotions` is a local schema extension |
| [RP-0019](#rp-0019) | P3 | Feature | Copy/paste blocks for LinkedIn and application forms |
| [RP-0022](#rp-0022) | P3 | Feature | Merge two specs — browse what sits between them |
| [RP-0024](#rp-0024) | P3 | Chore | `work[].stints` is experimental |
| [RP-0040](#rp-0040) | P3 | Chore | `work[].note` ignores the promo axis |
| [RP-0026](#rp-0026) | P3 | Feature | Per-skill confidence / weight |
| [RP-0029](#rp-0029) | P3 | Idea | Consume palettes from a brand kit (cross-project) |
| [RP-0031](#rp-0031) | P3 | Feature | Additive publish — keep several designs at once |
| [RP-0036](#rp-0036) | P3 | Feature | Items-per-page control |

## Done

*Entries describe what each item delivered at the time it closed, so figures in them
(test counts, the layout total, an axis list) are historical, not the current state — the
living numbers are in the docs.*

| ID | Title | Closed |
|---|---|---|
| RP-0033 | **Every axis is a multi-select filter.** An axis now holds a *set*: empty is unconstrained, several values are an OR, and axes combine with AND — so a "hold" is just a selection of one, which generalises RP-0037 rather than replacing it. Driven from the header (a colour swatch bar, plus a dropdown per remaining axis, each carrying a count badge) **or by clicking any chip on a card** — the real "more like this one" gesture. `space.matches` accepts a list per axis, `/api/page` takes repeated params (`?palette=moss&palette=plum`), and the vestigial `pin()` name-rewriting from the overlay era is gone. Chrome decisions: **colour keeps swatches** (a swatch *is* the value); everything else is a dropdown, because they are words either way. **A popover, not a panel** — opening one moves the header **0px**, measured. One verb for reset (`Clear` per axis, `Clear all`), always present but disabled, so the row never shifts. Pill rows **wrap evenly** (7 items go 4+3, then 3+2+2) since flex wraps greedily. Header costs +14px at rest (115→129). 215 unit tests, 38 acceptance checks. | 2026-07-23 |
| RP-0035 | **Counts follow the filtered set.** The header total and page count were derived from the full enumeration (`space.TOTAL`, 10,080 / 420 pages) and so were static under a hold. Now `space.total(filters)`/`space.pages(count, filters)` compute over the filtered subset, `/api/page` returns the live `total`, and the viewer updates both as holds change — "1,440 layouts · holding moss · page 1 of 60", back to 10,080 / 420 on release. Landed with the RP-0033 hold-as-filter slice. Unit-tested in `test_space.py`; acceptance asserts the HTTP total/pages drop under a hold. | 2026-07-23 |
| RP-0037 | **Typeface hold — the colour pin's twin.** A second always-on "hold this axis" bar (`#typeface`) mirroring the colour bar, on the second name segment. Typeface is a closed four-value axis, so no font picker is needed: four `.tf` **sample chips** (`grotesk humanist charter mixed`), each rendered *in its own face*, plus "Varied". Clicking one swaps the typeface segment of every card's spec and re-renders in place; the pin **persists across paging** and **composes with the colour pin**; the detail dialog carries the same bar. Colour and typeface now share one `pin()` that swaps name segments 0/1 (was `recolor`; `CAN_RECOLOR`→`CAN_PIN`). Covered by two unit tests (offers-every-typeface, typeface-segment-swap) and a real-browser dump-DOM acceptance check; live click-through driven in-browser (charter re-typed the grid, moss+charter composed and held across paging). | 2026-07-23 |
| RP-0012 | **Publish decision — went public.** The repo was `kebab-case` and named for its destination, so publishing was a visibility flip, not a rename. Ran `taking-a-repo-public.md` end to end: a secrets scan and private-content sweep across the tree *and* full history (every commit's author and committer reauthored to the GitHub noreply — a `user@hostname` default had crept in), the structural pre-flight (LICENSE, description, CI, prose README title, absolute `llms.txt` links), and a polish pass — all clean. Flipped with `gh repo edit --visibility public`, then verified the three paths that only exist once public: an unauthenticated clone, `pip install git+https://…` into a clean 3.11+ venv, and the Tests badge rendering. Recorded the flip in `.meta/code-manifest.md`. | 2026-07-23 |
| RP-0017 | **README + `llms.txt`, agent-forward.** Written from the concept and matched to the shape of `terminal-launcher` and `claude-statusline-kit`: one-line value proposition, badges, the problem in the reader's terms, a screenshot, the six-word vocabulary, requirements, install, a "hand it to your coding agent" paste block, a command table, roadmap, docs index. Plus `llms.txt` so an agent can orient without cloning. The screenshot renders the generic test fixture, never a real resume. | 2026-07-21 |
| RP-0002 | **Tests + CI.** 120 tests: the space (enumeration, naming round-trip across all 5,040, distance/neighbour invariants, deterministic spread), rendering (every spec renders, ATS claims hold, escaping, purity), every lint rule, both viewer deliveries, the scaffold, and PDF text extraction via PyMuPDF. Also two docs-match-the-code tests that would have caught the broken shipped quickstart. Workflow added for macOS + Linux × Python 3.11/3.13 — **unverified until first push**. | 2026-07-21 |
| RP-0010 | **Retire the hand-written themes** — found already resolved: `slate` is a palette and `editorial` a preset, both ordinary specs. There is no second theme system. | 2026-07-21 |
| RP-0015 | **One viewer, two deliveries** — `catalogue.py` and `explore/ui.py` collapsed into `viewer.py`, parameterised by preview source and whether export is offered; the `explore/` package is gone. A test asserts the two deliveries differ *only* in those two switches. | 2026-07-21 |
| RP-0020 | **Spec names are written out in full and stable** — `palette-typeface-header-skills-promo-density`, replacing an index-encoded scheme that renamed thousands of specs whenever an axis gained a value, breaking every saved or published reference. Also deleted two unused samplers and made `spread` linear rather than cubic. *(Recorded as RP-0023 until 2026-07-23, when the collision with the open architecture ticket of that number was repaired — RP-0020 had never been issued.)* | 2026-07-21 |
| RP-0011 | **Retire the PDF gallery** — replaced by `catalogue.py`: static, HTML previews, `file://`-browsable, builds instantly instead of ~1s per variant. | 2026-07-21 |
| RP-0021 | **Generated layouts are publishable** — `themes.get()` resolves spec names, so a layout found in the catalogue can be published. Previously the generated half of the space was previewable but unreachable from every other command. | 2026-07-21 |

## Details

### RP-0001 — Import an existing resume {#rp-0001}
**P1 · Feature · import**

PDF/DOCX → `resume.json`. The adoption cliff for this whole category: JSON Resume, HackMyResume and RenderCV all require hand-authoring structured data before anything works, which is why their download counts are in the hundreds. Extraction — unlike editing — has a **checkable oracle**: every extracted string must appear in the source text, so a hallucinated field can be rejected before it reaches the data. Ship the verifier alongside the extractor, not after. Sequence **RP-0025** (import as a skill) first.

### RP-0003 — Remix: pin a layout and vary one axis at a time {#rp-0003}
**P2 · Feature · explore**

Mostly a UI affordance: `space.neighbours(spec, radius=1)` already returns exactly the 20 one-axis variations. Needs an axis-picker in the card/detail view and a "vary this axis" strip showing each alternative rendered inline. Shares the axis-control surface with RP-0004 and RP-0022.

### RP-0004 — Global style locks + loadouts {#rp-0004}
**P2 · Feature · explore**

Pin axes (e.g. always `charter` + `moss`) so browsing covers only the remaining subspace — with the samplers gone this is a filter over the enumeration, not a change to a sampler. "Loadouts" are named partial specs (pure data) offering a middle ground between one-click themes and per-axis fiddling. Shares the axis-control UI with RP-0003 and RP-0022. The `.resume-pipeline.json` sidecar's schema was left room to grow from one remembered choice to a set of named ones (`{last, saved: {…}}`) — that growth belongs here, not in RP-0030.

### RP-0005 — A content design space, alongside the style space {#rp-0005}
**P3 · Feature · model**

Today a `Spec` describes only *presentation*. Section ordering, per-section short/long bullet variants, and which subset of the master skill list renders are all *content* choices, and the explorer should browse the product of both spaces. Precondition for the drag-and-drop builder (RP-0006).

**Scope narrowed 2026-07-23 — skills selection moved to RP-0039.** This ticket used to also claim per-variant *skills curation* ("selection over the master profile, never deletion from it"). That slice became urgent on its own — a 33-skill profile against guidance of 8–12, with deletion forbidden by rule — so it was carved out as **RP-0039** and raised to P1 ahead of this. RP-0005 remains the home for the **general** content space: section ordering, bullet variants, and browsing content × style as one product. Don't re-implement skill selection here; consume RP-0039's.

### RP-0006 — Drag-and-drop builder {#rp-0006}
**P3 · Feature · ux**

Reorder sections and swap between interchangeable section versions directly, "loadouts" style. Sits on top of RP-0003/RP-0005: once content is an axis set, direct manipulation is a second editor over the same model rather than a parallel implementation. Do not start before RP-0005.

### RP-0007 — Provenance model {#rp-0007}
**P1 · Feature · safety**

Track per-claim whether a value is a human-asserted fact or model-generated prose, and require explicit confirmation before any *new* figure can render. The genuinely unfilled gap in this space — no tool ships it — and the necessary counterweight to a linter that asks for metrics, which otherwise pressures a model into inventing them.

**Kept at P1 (2026-07-23):** considered for demotion as "important but not next" and deliberately held. Import (RP-0001) is the ticket that most *increases* the fabrication surface, so promoting import while demoting its counterweight moves in the wrong direction. The two are coupled.

### RP-0008 — Explain what an ATS actually is {#rp-0008}
**P2 · Feature · docs**

And a how-to guide. Must be evidence-first: the widely-cited "75% of resumes never reach a human" traces to Preptel, a vendor that folded in 2013 without publishing a study. Document the *mechanism* (parsers extract top-to-bottom, left-to-right, so multi-column layouts interleave) and explicitly debunk the magnitude claims rather than repeating them.

### RP-0009 — Cover letters {#rp-0009}
**P2 · Feature · render**

Same data model plus a job posting; the reason RenderCV was not adopted (its schema cannot express them). Needs a letter document type, a shared identity/contact block with the resume, and per-application storage under `Applications/`. If cover letters warrant their own agent skill, that scope lives here — not in RP-0025.

### RP-0013 — Lint variants, not the master profile {#rp-0013}
**P3 · Feature · lint**

`skills/bloat` currently fires against `resume.json`, but the master profile is *supposed* to be a superset — the warning belongs on a rendered variant. Today the rule has no sanctioned remedy: the only way to satisfy it is a deletion the profile forbids.

**Unblocked by RP-0039, not RP-0005 (revised 2026-07-23).** This used to say "Requires RP-0005", but it doesn't need the whole content space — it needs a rendered variant to carry *its own skill set*, which is exactly what **RP-0039** delivers. Once that lands, `skills/bloat` has something meaningful to fire against and can be re-pointed at the variant. RP-0005 remains a later generalisation, not a precondition.

### RP-0014 — `work[].promotions` is a local schema extension {#rp-0014}
**P3 · Chore · model**

JSON Resume has no field for in-company progression, and its hosted registry validates against a stricter draft-04 schema with `additionalProperties: false`, so this would be rejected there. Harmless locally (we do not use the registry), but document it, and check for an upstream field before it spreads.

### RP-0016 — Keep the hosting path open {#rp-0016}
**P2 · Chore · architecture**

A hosted version is plausible later, so nothing should assume a local filesystem or a single user. Currently sound: rendering is pure (`compose.render(resume, spec)`), the server speaks a small HTTP API, and it now holds **no per-user session state at all** — the sampler and its verdict file are gone, so there is nothing to scope to a user. Currently not: the cache directory and `find_resume`'s upward walk are single-user assumptions, and `pdf.py` shells out to a local Chrome. Audit and document the boundary — do not build hosting, just avoid foreclosing it.

**Raised P3 → P2 (2026-07-23):** RP-0038 ships a static demo that directly exercises this boundary, so the audit stopped being hypothetical.

### RP-0018 — UI/UX pass on the viewer {#rp-0018}
**P1 · Chore · ux**

Feedback: it "could use a lot of tuning and refining". Now unblocked — RP-0015 means there is one surface to polish rather than two that disagree. Settle empty/error states, loading behaviour while iframes render, and keyboard affordances currently discoverable only from a hint strip. The stated aesthetic is modern — pills, icons, chips — so the axis chips are the obvious place to start.

**Raised P2 → P1 (2026-07-23):** RP-0038 makes the viewer the **first impression for everyone**, not just for people who already installed it — polish stops being optional the moment there's a public link.

**Header slice landed 2026-07-23.** The hero-shot review found the header was a five-item left-aligned stack (title, statusline, colour bar, type bar, a three-line explanatory paragraph) with the entire right side below the nav empty — so it read as cluttered on the left, barren on the right, and pushed the grid down. Two fixes shipped:

1. **The header is a two-column grid** (`.hdr`) — identity on the left (title, status, explainer toggle), controls on the right (paging/nav, colour bar, type bar). The hold bars leaving the left gutter is what stops the header being one tall stack.
2. **The explainer is collapsible and remembers.** It's pure onboarding copy, so it shows on a first visit and stays hidden once dismissed (`localStorage`), rather than sitting permanently between the controls and the product.

Measured result: **header height 230px → 115px**, so a full row of cards (tags *and* the Open / Copy Name buttons) is visible where the old shot cut cards off mid-content. Verified live at 1500 / 760 / 620px — the nav still holds row 1 under the longest status text, which was the RP-0035/0037 regression risk. Hero shot regenerated. Covered by product-map rows 9 and 10.

**Still open here:** empty/error states, loading behaviour while the iframes render, and the keyboard affordances currently discoverable only from the hint strip. The axis chips themselves — pills, icons — have not been restyled.

### RP-0019 — Copy/paste blocks for LinkedIn and application forms {#rp-0019}
**P3 · Feature · export**

LinkedIn does not expose profile editing over its official API (see the workspace's `linkedin-api-cli.md`), so syncing a profile to a resume is manual by necessity. The value beyond a text dump is **per-field character limits, checked before paste** — cross-checked July 2026 as headline 220, About 2,600, experience description 2,000, skill 80, with About collapsing behind "See more" at ~300 chars. Those are third-party figures; LinkedIn does not publish them, so they need a date-stamped source and re-verification. Extends to Workday/Greenhouse/Lever, which want the same fields with different limits. *Built once and reverted 2026-07-21 — premature; see commit history for a working implementation.*

### RP-0022 — Merge two specs {#rp-0022}
**P3 · Feature · explore**

Pick two layouts you like and browse what sits between them. Despite first appearances this is not a random operation: two specs differing on *k* axes span exactly **2^k** specs — every combination taking each axis from one parent or the other — so the whole offspring set can be **enumerated** rather than sampled. Mechanically it is a facet filter constraining each axis to `{a.value, b.value}`, i.e. the single-axis pin of RP-0003 generalised to two pins, so it needs no sampler, no randomness and no session state. `space.distance` already gives *k*. Depends on the same axis-control UI as RP-0003/RP-0004.

### RP-0023 — Work without a local download, install or clone {#rp-0023}
**P2 · Feature · architecture**

Everything today assumes a checkout and a Python environment, which is a real barrier for the audience most likely to want this — someone with a resume and no interest in a toolchain. Options, roughly in ascending cost: a hosted instance (the concept already forbids assuming a local filesystem or single user — rendering is pure and the server holds no session state, so the boundary is mostly kept); running the renderer in the browser via WASM/Pyodide, which keeps the "no server sees your resume" property; or a zero-install agent path where a coding agent fetches and runs it without a persistent install. Decide what "no install" should *mean* before building any of them — the answers differ on where the profile lives, which is the actual question.

**RP-0038 is the cheap first slice** of this — a static fixture demo delivers the "try it with no install" property without settling the larger question. This ticket remains the *decision*.

### RP-0024 — `work[].stints` is experimental {#rp-0024}
**P3 · Chore · model**

Ships and is tested, but is a local extension JSON Resume has no field for, and no real document has exercised it yet — the author's own resume was migrated to it and then migrated back, because a flat bullet list plus a `note` said what he wanted with less machinery. Before promoting it: confirm it earns its keep on a document that genuinely needs per-title bullets, and check for an upstream field first (see RP-0014). Do not build further features on it until then.

### RP-0025 — `import` as a skill, not a parser {#rp-0025}
**P1 · Feature · ux**

*(Re-scoped 2026-07-23.)* The original ask — split the one `career` skill into a family, one per verb — was partly done and partly rejected. **Done:** the split-by-intent skills were renamed verb-forward, `career-resume-update` (edit/lint/publish) + `career-layouts-browse` (ADR-0011). **Rejected:** going further to one micro-skill per verb (`career:lint`, `career:publish`, …) — lint and publish are steps of an update, not standalone jobs, and fragmenting them would split the anti-fabrication rule across skills and create matcher ambiguity.

What survives is the genuinely valuable piece: **`import` (RP-0001) as a skill rather than code.** An agent already reads PDF and DOCX, so the skill supplies the extraction rules, the JSON Resume shape, and crucially the verification step (every extracted string must appear in the source, so a hallucinated field is rejectable) — a far cheaper route to the biggest gap than a parser. Sequence before RP-0001 and re-scope it afterwards. Cover letters, if they warrant a skill, are RP-0009, not here.

**Raised P2 → P1 (2026-07-23):** it is the cheap enabler explicitly sequenced *before* RP-0001. A P1 ticket's unblocker cannot sit at P2.

### RP-0026 — Per-skill confidence / weight {#rp-0026}
**P3 · Feature · model**

A number on each skill saying how strongly the person would claim it, so per-variant curation can surface the right subset for a target role instead of the whole master list — the missing input to **RP-0039**'s selection (and through it RP-0013).

**An input, not a precondition (2026-07-23).** RP-0039 ships selection as a hand-picked set; weights would later make that selection *derivable* for a target role rather than hand-maintained. Don't gate RP-0039 on this. Two hard parts, both about *entry* rather than storage: rating 28 skills one at a time through an agent is miserable, so this wants a grid in the inspector — bulk, comparative, one screen — which means it lands **after** the inspector gains write access, not before. And a weight is a self-assessment, not a fact, so it must never be inferred on the user's behalf: an unrated skill stays unrated. Schema is trivial; JSON Resume already has a free-text `skills[].level`, so check whether that or a numeric extension is the right home.

### RP-0027 — Verify on Windows, then restore the badge {#rp-0027}
**P2 · Chore · quality**

`pdf.py` carries Windows browser paths and everything else is stdlib, so it *should* run — but nobody has, so the platform badge was cut to `macOS / Linux` (the two CI verifies) rather than claim what the sibling repos actually earned. Run the full workflow on Windows — `init`, `lint`, `catalogue`, `serve` (loopback + a browser), `publish` (the Chrome-family lookup is the likeliest snag) — fix what breaks, then add Windows back to the badge and to the README requirements, and flip its row in `platforms-and-status.md` from Unverified to Verified. Ideally add a `windows-latest` leg to CI so it cannot silently regress.

### RP-0028 — HEX / custom palettes: an open palette axis {#rp-0028}
**P2 · Feature · viewer**

The colour bar swaps among seven built-in palettes (`compose.PALETTES`), and the 10,080-layout enumeration works only because every axis is a *closed finite set*. Supporting a HEX value means letting a palette come from **outside** that set — so model it as an **overlay pinned like the existing colour-lock** (held constant while the other six axes browse), not an eighth enumeration entry, and the finite space is preserved. A palette is four coordinated colours (`accent, ink, tint, on_dark`), not one, so the picker needs either all-four entry or a rule to derive tint/ink/on-dark from a single seed accent by lightness. This is the small, shippable first instance of "a palette from an external provider" — the same injection point RP-0029 would later feed.

### RP-0029 — Consume palettes from a brand kit (cross-project) {#rp-0029}
**P3 · Idea · integration**

A planned "brand kit builder" (separate, larger project) produces named sets of coordinated colours — which is exactly what a palette is here. If it ships, the viewer's palette axis should be able to draw from a shared brand kit instead of (or alongside) the seven built-ins, so a resume stays on-brand with everything else the kit dresses. Mechanism unknown and deliberately unscoped; the concrete precursor is **RP-0028** (proving an external palette can be injected as an overlay at all). This ticket only marks the seam so the two are designed to meet rather than retrofitted. Do not build ahead of the brand kit existing.

### RP-0030 — Surface format choice in the viewer {#rp-0030}
**P2 · Feature · viewer**

`publish --formats` and the `.resume-pipeline.json` sidecar (ADR-0009) landed on the CLI side; the viewer's "★ Make this my resume" still always writes all three formats. Add a format toggle to the publish control so a viewer-driven publish records the same `{layout, formats}` the CLI does. Also consider a `--formats all` convenience and a note when a bare publish's formats differ from what's on disk. The sidecar's growth toward **named loadouts** belongs in RP-0004, not here.

### RP-0031 — Additive publish: keep several designs at once {#rp-0031}
**P3 · Feature · publish**

`publish` is deliberately replace-in-place: one canonical deliverable, overwritten each time (ADR-0004/0009), now with the previous version snapshotted to `Archive/` (ADR-0010). But there may be a case for *keeping* multiple published designs live side by side — e.g. a print variant and an ATS variant, or per-audience versions — rather than one-at-a-time. That is a different model (named, coexisting deliverables) and reopens "which file do I send?", so it needs a naming scheme and a way to mark the primary. Also fold in the archive refinements deferred from ADR-0010: dedupe identical consecutive publishes, and prune old snapshots. Speculative — no concrete demand yet.

### RP-0032 — Lead with a small, diverse set {#rp-0032}
**P1 · Feature · explore**

10,080 layouts across 420 pages is too much to meet at once. The per-page count is not the problem — the grid already shows 24 at a time (RP-0036 makes that adjustable) — the *haystack* is: paging linearly through 420 pages of near-identical neighbours is not how anyone picks a resume. Land instead on a **maximally-diverse handful**: `space.spread(n)` already samples across every axis, so the first screen can be ~20 layouts chosen to span palette/typeface/header/density rather than the first 20 of enumeration order. Pair that with filtering (RP-0033) and named styles (RP-0034) as the real navigation — *narrow, then browse*, instead of browsing everything. This is the umbrella UX ticket those two serve.

### RP-0042 — Group the grid by an axis {#rp-0042}
**P2 · Feature · explore**

The half of RP-0033 that did not ship. Filtering landed — every axis is a multi-select, driven from the header or a card's chip — but **clustering the grid by an axis** did not: showing the page broken into labelled runs ("all the `band` headers, then all the `masthead`"), so structure can be compared rather than scanned.

Open questions it inherits: whether grouping is a *view* over the current filtered page or a re-query that returns a page per group; whether more than one axis can group at once (probably not — two nested groupings is a pivot table, not a browse); and how it interacts with paging, since a group can straddle a page boundary. Sits on the axis-control surface RP-0033 built, so the values and labels already exist.

### RP-0034 — Named styles / archetypes as browse entry points {#rp-0034}
**P2 · Feature · explore**

"Minimalist", "Bold", "Editorial". A *style* is a named bundle of axis constraints (a partial spec) — the "loadouts" of RP-0004 seen from the discovery side: instead of pinning axes by hand, the user says "show me Minimalist" and the space filters to that archetype. Sits on top of RP-0033's badge-filtering. Open questions: is the style set **hand-curated** (a dozen tasteful presets) or **derived** from axis combinations; is a style a **hard filter** (only matching layouts) or a **soft ranking** (nearest-first); can a chosen style then be loosened one axis at a time (back into RP-0033). Start hand-curated + hard-filter — the cheapest useful version.

### RP-0036 — Items-per-page control {#rp-0036}
**P3 · Feature · viewer**

The grid is fixed at 24 live renders per page (`serve(…, count=24)`); let the user pick — e.g. 12 / 24 / 48 — from the viewer. Trade-off to surface: each card is a live iframe render, so more per page means more to render and scroll (24 was chosen as the balance). Self-contained — the page count already follows `count` (`space.pages(count)`). Interacts only with RP-0032 (the diverse default set).

### RP-0043 — Filter bar regressions {#rp-0043}
**P1 · Bug · viewer**

Two misses introduced by `171f20c` ("one filter bar, Color, explainer below the controls"). Both were visible immediately in the browser and are **regressions against the state at `f8bd48f`**, which was better. Everything needed to fix them is written down here.

**1. The filter bar should be two rows, not one flowing bar.** The feedback was that the filters "should not be separate from the Color" — that meant they should read as **one group**, not that they should be merged into a single wrapping row. The intended shape is:

```
row  Color   ● ● ● ● ● ● ●
row  Type ▾  Header ▾  Skills ▾  Promo ▾  Density ▾  Group ▾   ✕ Clear all
row  What is this?
```

Colour keeps its own row; the six dropdowns keep theirs; the two read as one group by sitting adjacent and sharing alignment, **not** by being concatenated into one `#filters` flex container. `171f20c` collapsed them into one bar, which at any width narrow enough to wrap interleaves swatches and pills across rows and looks worse than what it replaced. "What is this?" moving below the controls was correct and should stay.

**Mechanically:** restore the two containers (`#palette` and `#axes` at `f8bd48f`, or two children of a shared wrapper), keep the `.swgroup` idea so a wrap can never split the label from its swatches, and keep `balanceWrap` on the dropdown row. The single-column media query below 900px still applies to both.

**2. The pager must never wrap.** `« ‹ Shuffle ›` now breaks across lines at narrow widths; it did not before. `.nav` needs `flex-shrink:0` (and the row that holds it must let it keep its width) so the four controls stay on one line at every width — the same invariant RP-0018 established when the status text was moved to its own line, now broken from the other direction. Regression-checklist row 9 covers exactly this and must be re-verified.

**Also open (deliberately deferred, not forgotten):** `171f20c` removed the colour-specific `Clear`, on the reasoning that swatches toggle directly and `Clear all` sits nearby. With colour back on its own row that reasoning weakens — decide whether it returns.

**Not a regression, but decided here:** the UI says `Color` while the docs and comments say "colour". The repo is written in British English throughout, so a repo-wide sweep is its own call; the mixed state is intentional until then.

### RP-0038 — A hosted GitHub Pages demo {#rp-0038}
**P1 · Feature · hosting**

Fixture data, click-around, no backend. Ship a static site (GitHub Pages, matching RP-0023's static-first lean) that serves the viewer over a **fixture profile**: browse the whole design space, hold colour/type, page, open layouts — nothing real behind it. First value is a shareable "try it" link that needs no install (the RP-0023 barrier). The grid already builds client-side; the one server piece is `/preview` and PDF export — for a static demo, pre-render the fixture's previews (or move rendering into the browser).

**Long-term arc:** grow it into *upload/import a resume (or paste JSON Resume) → browse layouts → export/save*, with browser-local state (eventually accounts) so the whole flow runs in the page and no server sees the resume — the privacy property RP-0023 wants. Sequence: the fixture demo first (cheap, high signal); the import/export flow after RP-0001. Enriches RP-0023 and RP-0016.

**Raised P2 → P1 (2026-07-23):** the cheapest thing that changes the project's *reach* — it attacks RP-0023's install barrier at a fraction of the cost. Land **RP-0018** before or alongside it: a public link makes the viewer everyone's first impression.

### RP-0039 — Publish a subset of skills without deleting from the profile {#rp-0039}
**P1 · Feature · model**

The master profile is a superset *by design*, and the rule is **never delete a skill from it** — but nothing renders a *subset*, so in practice the profile can only ever grow, and `skills/bloat` fires with no sanctioned remedy. The two rules collide: the only way to shrink what publishes is a deletion the profile forbids.

Hit for real on 2026-07-23 — adding an `Agentic Engineering` bucket took a profile to **33 skills** against guidance of 8–12, and every low-signal entry crowding it out (`VSCode`, `SSMS`, `Jira`) was unremovable by rule. The user's framing: *"I don't want to cut low-value skills from the JSON, but I want to manage and publish the high-value ones."*

Scope is deliberately **narrower than RP-0005**: choose which skills publish. Not section ordering, not short/long bullet variants, not a browsable content space.

**Minimal shape — selection is data an agent edits; no UI.** Two candidate homes, and picking between them is this ticket's real question:

- a per-skill flag in `resume.json` — content, travels with the profile, visible in diffs; or
- a selection list in the `.resume-pipeline.json` sidecar — tool state, matching ADR-0009's precedent for remembered choices, keeping the profile pure. Also generalises to *per-target* selections later (one set for backend roles, another for agentic ones).

**Explicitly deferred: visual/bulk management of the master list.** Selecting 30+ items one at a time through an agent is miserable — same reasoning as RP-0026 — so that wants a grid or inspector screen, and it lands after the inspector gains write access. Agent-plus-JSON is the acceptable interim.

Carves the urgent slice out of **RP-0005**, which stays the home for the general content space. Partially unblocks **RP-0013**: once a rendered variant has its own skill set, `skills/bloat` finally has something meaningful to fire against. **RP-0026** (per-skill weight) is the better *input* to selection later, not a precondition.

### RP-0040 — `work[].note` ignores the promo axis {#rp-0040}
**P3 · Chore · model**

`_note()` hardcodes `class="promo-inline"` and never consults `spec.promo`, so a note renders identically under `badge`, `ladder`, `stacked` and `inline`. The axis that exists to govern *how a promotion is shown* does not reach the one field most documents actually use — RP-0024 records that the author's own resume migrated to `stints` and then back, because "a flat bullet list plus a `note`" said what he wanted. `note` is the common path; `stints` is the exception.

The consequence is that **any** change to note presentation is necessarily global. On 2026-07-23 the note was given the accent at full weight (a `.note` rule, deliberately scoped away from `.promo-inline` because that class also lands on the *stints container* when `promo=inline`, where accenting a whole block of titles would be wrong). The scoping is correct, but the styling still applies to all 10,080 layouts: a taste decision baked into the whole space rather than offered as a choice, which inverts how every other presentation decision in this tool works.

What to decide:

- **Route note presentation through `spec.promo`** — each promo value styles its own note, and an emphasised treatment becomes a fifth value, added rather than imposed. Cheaper, and reuses an axis whose meaning already fits.
- **Or admit a note is not a promotion treatment at all** and give it its own axis. Honest to the model, but widens the space for a single line of text.

Check for an upstream JSON Resume field before either (same caution as RP-0014). Sits with **RP-0014** and **RP-0024** as the unsettled promotion-model cluster; none of the three should be resolved without the other two in view.

### RP-0041 — Bundle deterministic fonts {#rp-0041}
**P1 · Feature · render**

Every typeface value is a **system font stack**, so the same spec renders in a different font on a different machine. Measured in a real browser on the author's Mac, 2026-07-23:

| Value | Resolves to on macOS | Resolves to on Windows |
|---|---|---|
| `grotesk` | Helvetica (`Segoe UI` absent) | Segoe UI |
| `humanist` | Optima | Candara (`Optima` absent) |
| `charter` | Charter | Georgia (`Charter` absent) |

**Why this is a correctness bug, not a polish item.** ADR-0003 makes spec names *stable and shareable* — "save it, share it, publish against it". But `harbor-charter-band-…` is a Charter document on macOS and a Georgia document on Windows: **same name, materially different resume**. The guarantee is only skin-deep. `pdf.py` shells out to the *local* Chrome, so the published PDF embeds whatever resolved on the machine that ran it — two people publishing the same layout get different deliverables.

**Fix — ship the fonts, embed only what a document uses.** Pre-subset open-licensed (OFL) WOFF2 faces into the package; at render time base64 the two or three faces the chosen spec actually needs. `base64` is stdlib, so **"zero runtime dependencies" survives** — the subsetting happens once, offline, not at render time (no `fonttools` at runtime). Embedding as `data:` URIs keeps the HTML deliverable **self-contained**, which ADR-0004's "one file you send" requires; referencing external font files would break a resume the moment it is emailed. Budget: ~4 faces ≈ 150KB inlined per document.

**Candidate set** — keeps the existing names honest where an open equivalent exists:

| Value | Font | Note |
|---|---|---|
| `grotesk` | Public Sans | neutral grotesk |
| `humanist` | Source Sans 3 | replaces the Optima / Candara lottery |
| `charter` | XCharter or Charis SIL | open Charter derivatives — the name stays true |
| `garamond` | EB Garamond | old-style serif; new value |
| `slab` | Zilla Slab | a texture the set lacks; new value |
| `plex` | IBM Plex Sans + Serif | strong pairing; new value |
| `mixed` | serif display / sans body | as today, but deterministic |

**Cost to weigh:** each typeface multiplies the whole space — 4 → 7 values takes 10,080 → 17,640 layouts. On-thesis ("adding a value multiplies the catalogue"), but it makes **RP-0032**'s overwhelm problem larger, not smaller. Adding values is also the exact scenario ADR-0003's naming scheme was designed to survive, so it should cost nothing structurally.

**Interacts with:** **RP-0038** — a hosted demo renders per-visitor-machine until this lands, so the demo would not show what you actually get. **RP-0027** (verify on Windows) — this is the class of divergence that pass would have caught. **RP-0033** — the typeface filter's sample chips can only depict a face the renderer will actually use. **RP-0028** (custom palettes) is the colour-axis sibling of the same "closed set vs open input" question.

**Open:** licence review per face (OFL attribution requirements in the published artefact), whether italics are needed or synthesised, and whether the `mixed` pairing should be re-chosen once the set changes.

## Conventions

The house standard for this board's shape — lanes, schema, detail tiers, archiving — is
`.meta/ticket-board-standard.md` in the author's workspace. The essentials, so this file
stands alone:

- **Source of truth is this file.** Edit the tables directly, then regenerate the render:
  `python docs/render.py docs/tickets/tickets.md`. Commit both files together.
- **IDs** are `RP-NNNN`, one sequence, assigned in creation order (not priority), never
  renumbered and never reused.
- **Lanes**, in order: In progress · On deck · Blocked · Backlog · Done. An empty lane keeps
  its heading and reads `*(none)*`.
- **Priority:** P1 (soon) → P2 (real, not next) → P3 (someday). **Type:** Bug · Feature ·
  Chore (housekeeping — tests, refactors, packaging, docs) · Idea (not yet scoped).
- **Rows are sorted by priority**, ties by ID — except **On deck**, which is in intended
  sequence, and **Done**, which is reverse-chronological.
- **Keep rows short — length is the signal.** A row is a pointer, one sentence. Anything
  longer gets a `### RP-NNNN` block under **Details** (ID-ordered), which is also the only
  place the ticket's *area* appears. `Done` rows are exempt — there the row *is* the record.
- **A literal `|` in a cell spawns a phantom column** — the renderer splits rows naively.
  Use `/` inside cells.
