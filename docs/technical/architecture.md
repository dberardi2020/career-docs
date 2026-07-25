# Architecture

The shape of the code, the flow through it, and the seams that matter. Per-module detail is in
[`module-reference.md`](module-reference.md).

## In one line

**Rendering is a pure function — `compose.render(profile, spec) -> str`.** Every surface is a
different way of calling it, and none of them owns the data.

That is the whole architecture. It is why a preview cannot drift from what publishes, why
there is no cache to invalidate, and why the server needs no per-user state.

## Layers

```
                 cli.py                        the substrate an agent drives
                   │
     ┌─────────────┼──────────────┬──────────────┐
     │             │              │              │
 catalogue.py   server.py    deliverable.py    lint.py        surfaces
     │             │              │              │
     └──── viewer.py ─────┐       │              │
                          │       │              │
                   compose.render(profile, spec) │            the pure core
                          │       │              │
              ┌───────────┴───┬───┴────┐         │
           compose.py     markdown.py  pdf.py    │            renderers
              │                                  │
           space.py ─────────────────────────────┘            the space
              │
           model.py                                           the data
```

Dependencies point downward only. `model.py` imports nothing from the package;
`compose.py` imports `model`; `space.py` imports `compose`. Nothing in the core knows a
surface exists.

## End-to-end flow

**Browsing.** `cli` locates the profile → `model.load` validates it → the space is ordered
for browsing (`space.browse_order`, a hash sort so pages are well-mixed and deterministic) and
sliced into a page (`space.page`) → `viewer.page` builds one HTML page embedding those specs →
each card is an `<iframe>` whose content is `compose.render` output, either written beside the
page (`catalogue`) or served on request (`server`). The static catalogue instead shows a
`space.spread` — a fixed, representative sample rather than a place in a sequence.

**Publishing.** A spec name arrives from the CLI or the viewer → `space.parse` decodes it →
`deliverable.write` renders HTML, Markdown and PDF, and writes all three beside the profile.

**Linting.** `lint.check(resume, theme=...)` walks the profile and the layout's declared
claims and returns `Finding` objects. It never mutates.

## The seams

Four places where the design deliberately leaves a joint.

### `render(profile, spec)` is pure

No IO, no globals, no clock. Same inputs, same bytes — asserted by test. This is what makes
previews trustworthy and what would make a hosted version possible.

### The space is data, not code

`space.py` knows nothing about HTML. It computes distance, neighbours, spread and name
parsing over `Spec` — a frozen dataclass of categorical values. Adding an axis value touches
one list in `compose.py`; the space grows and everything else follows.

### One viewer, two deliveries

`viewer.page(specs, resume, preview=..., exportable=...)` is the only UI. The two callers
differ in exactly two switches: where a preview comes from (a sibling file, or a `/preview/`
route) and whether the page can act. A test asserts those are the *only* differences, because
this was two implementations that had begun to drift. See
[`../decisions/0004-one-viewer-two-deliveries.md`](../decisions/0004-one-viewer-two-deliveries.md).

### The browser is behind `pdf.py`

The one external dependency. `find_browser()` resolves it at runtime across macOS, Windows and
Linux, honouring `CAREER_DOCS_CHROME`, and raises `BrowserNotFound` rather than failing
obscurely. Everything except PDF works without it.

## The server holds no session state

`server.py` builds a context dict at startup — the output directories, the page size, the
profile path — and keeps **no per-user session**: no favourites, no verdicts, no persisted
batch. The page you are on lives in the URL you request (`/api/page?i=…`), not in server
state. A test asserts the context keys, so a session cannot creep back in.

One thing it *does* re-read: the **profile**, on every request, when its mtime changes. An
agent is expected to be editing it while the viewer is open — that is the premise — so a copy
cached at startup would mean silently showing a document that no longer exists. A malformed
edit caught mid-write is ignored in favour of the last good copy rather than blanking the
page.

This all falls out of [`../decisions/0002-browse-not-search.md`](../decisions/0002-browse-not-search.md),
and the no-session part is what keeps a hosted future open: there is nothing here that would
need scoping to a user.

## Where a hosted version would strain

Not built, and deliberately not foreclosed (RP-0023). Currently sound: rendering is pure, the
API is small, no session state. Currently single-user:

- `cli.cache_dir()` writes under `~/.cache`.
- `cli.find_resume()` walks up from the working directory.
- `pdf.py` shells out to a local browser — the real obstacle.

## Print versus screen

A rendered variant has to be correct in two media, and they take different rules.

- **Print** — `@page` boxes set the paper margin. The `band` header bleeds a banner to the
  paper edge, which needs a zero-margin page; that is scoped to `@page :first` so later pages
  keep their margins.
- **Screen** — `@page` does not apply, so a `@media screen` rule mirrors the margin.

Both are asserted: a PDF test re-extracts text and checks every page's margin, and a CSS test
checks the screen inset across the space. Each of these was a real bug, and each was
invisible in the other medium.
