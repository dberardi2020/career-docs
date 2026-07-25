# 0007 — Keep the in-house renderer rather than adopting RenderCV

**Status:** Accepted · 2026-07-21

## Context

Structured data → themes → HTML/PDF has existed since 2013 and is more mature than anything
worth writing from scratch. Five parallel research tracks surveyed the landscape to answer
whether a home-built renderer was remaking a solved problem.

The answer: the **renderer** is solved, comprehensively. **RenderCV** was the strongest
candidate — Python, pip-installable, Typst rather than LaTeX since v2.0 (so no TeX toolchain),
offline, nine single-column themes, tagged PDFs with clean text extraction, 17k stars.

## Decision

Keep the in-house renderer. Adopt the **JSON Resume schema**; adopt nothing else.

## Rationale

**Cover letters decided it.** They do not fit RenderCV's schema, so adopting it means running
*two* rendering paths — RenderCV for the resume and something else for letters. One pipeline
that renders both documents from one data model beats a better resume renderer plus a bolted-on
second path.

Secondary: RenderCV's data model is its own YAML, so JSON Resume → RenderCV is one-way and
lossy; and it is bus-factor 1.

The deeper point is that **the renderer was never the product.** What this is built around is
a design space of layouts, a linter for the *layout*, and a workflow an agent can drive
safely. Buying out of renderer maintenance would not have bought any of those.

## Consequences

- Rendering is ours: `compose.render` plus a browser for PDF. Zero runtime dependencies.
- RenderCV's theme *designs* are worth learning from; adopting its code and schema is not
  what this needs.
- Building a general-purpose resume generator is an explicit non-goal: the renderer exists to
  serve the design space, not the other way round.
- **Revisit if** renderer maintenance becomes a burden, or if cover letters turn out to fit
  somewhere unexpected.
