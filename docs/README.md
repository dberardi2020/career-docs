# Documentation

The docs for `career-docs`, routed by what you came here to do.

**New to the project** → [`product/overview.md`](product/overview.md) — the problem, the
approach, and the design principles the rest of it follows.

**Trying to understand the words** → [`product/concepts.md`](product/concepts.md). Profile,
axis, spec, space, variant, deliverable. Everything else is written in those terms, so this
is the doc to read second.

**Going to use it** → [`product/user-guide.md`](product/user-guide.md) — install, first run,
the whole workflow end to end, and what to do when something breaks.

**Wondering whether it does the thing you need** →
[`product/platforms-and-status.md`](product/platforms-and-status.md). An honest ledger of what
works, what is experimental, and what is not built.

**Going to work on the code** → [`technical/architecture.md`](technical/architecture.md) for
the shape, then [`technical/module-reference.md`](technical/module-reference.md) for what each
file is responsible for.

**Wondering why something is the way it is** → [`decisions/`](decisions/README.md). The ADRs
carry the current decision state; `product/` and `technical/` synthesise it. **When they
disagree, the ADR is right and the synthesis is stale.**

**Looking for what is next** → [`tickets/tickets.md`](tickets/tickets.md).

## Layout

| Path | Holds |
|---|---|
| [`product/`](product/README.md) | What it is, who it is for, how to use it. |
| [`technical/`](technical/README.md) | Architecture, modules, data model, testing. |
| [`decisions/`](decisions/README.md) | ADRs — numbered, never renumbered, never reused. |
| [`tickets/tickets.md`](tickets/tickets.md) | The backlog. No external tracker. |
| `assets/` | Screenshots, and `demo-profile.json` — the fictional profile every screenshot renders. |

## Conventions

**MD + HTML in lock-step.** Prose docs exist as `name.md` (the source of truth) and
`name.html` (a styled render of the same content). Regenerate after editing:

```sh
python docs/render.py docs/product/concepts.md
```

Rendering is selective rather than exhaustive here — the board and the long-lived product
docs are paired; short internal notes need not be. `render.py` is stdlib-only.

**Filenames are lowercase kebab-case**, except `README.md`. Ticket IDs stay uppercase
(`RP-0007`) wherever they appear — they are identifiers, not prose.

**No `conventions.md` in this repo.** The cross-repo house standard is not kept inside one of
the repos it governs.
