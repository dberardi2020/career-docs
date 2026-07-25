# Career Docs

**Your career documents, kept as data.** Browse thousands of resume layouts, check them for
parse safety, and publish the one you pick — from inside your coding agent.

[![Tests](https://github.com/dberardi2020/career-docs/actions/workflows/tests.yml/badge.svg)](https://github.com/dberardi2020/career-docs/actions/workflows/tests.yml)
![platform: macOS | Linux](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-blue)
![python: 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![license: MIT](https://img.shields.io/badge/license-MIT-green)

Your resume is data, not a document. Keep it that way and two things follow: the file you
send never drifts from the file you edit, and how it *looks* becomes a choice you make from a
whole space of layouts rather than a list.

This keeps one structured **profile** as the only thing you edit, generates a **space** of
10,080 layouts from it, and lets you browse that space until something looks right. The
editing happens through your agent: you say what to change, it changes the data. Publishing
writes one deliverable — PDF, HTML and Markdown — from the layout you chose.

**Resumes are what works today.** The workspace `init` scaffolds already holds your cover
letters and applications, and the name says where this is going — but the resume is the part
that is built.

![The layout viewer: a row of resume layouts, each a live render of the same profile in a
different design, its axis values shown as chips beneath it — the active filter's chip
highlighted on every card. The header keeps identity on the left (the title, and the filtered
size "1,440 of 10,080 layouts") and the controls on the right: paging, a colour swatch bar with
green selected, and a dropdown per remaining axis](docs/assets/viewer-v2.png)

### Layouts are generated, not templates

There is one renderer and seven independent choices: **palette, typeface, header, skills,
promotions, density, grouping**.

A **spec** is one combination of the seven, and every combination renders — which is where
10,080 comes from. Add one value to one choice and the whole space multiplies.

### Moving through it

Page through a screen at a time, or **Shuffle** to land somewhere else entirely.

**Every axis filters.** Pick two colours and a typeface and the browse drops to just those
— 10,080 → 720 — with the count and paging following what you picked. Filter from the header,
or click any chip on a card to say "more like this one".

### What is distinctive here

Layouts as a **design space** rather than a theme list. A linter that checks the **layout**
for parse safety, not just the content. And a workflow built for an agent to drive rather
than a human to type.

## Model, in six words

- **Profile** — your resume as structured data ([JSON Resume](https://jsonresume.org/schema)).
  The only file you edit. A *superset*: it holds everything you have ever done, including
  what no single resume would show.
- **Axis** — one independent presentation choice. Seven of them: palette, typeface, header,
  skills, promo, density, grouping.
- **Spec** — one point in the space, a value on every axis, named in full:
  `harbor-grotesk-band-pills-ladder-airy-grouped`. Pure data — save it, share it, publish
  against it.
- **Space** — the product of the axes. **10,080 layouts**, enumerated rather than curated.
  Combinatorial, not curated: 28 hand-authored axis values over one skeleton.
- **Variant** — a profile rendered through a spec. What you look at. Cheap and disposable.
- **Deliverable** — the one published output you actually send.

The full concept model is [`docs/product/concepts.md`](docs/product/concepts.md).

## Requirements

- **Python 3.11+**. Zero runtime dependencies — everything is stdlib.
- **A Chromium-family browser** (Chrome, Chromium, Edge, Brave) — used only for PDF export,
  and located at runtime. Everything else works without one.

## Install

**Recommended** — with [pipx](https://pipx.pypa.io):

```sh
pipx install git+https://github.com/dberardi2020/career-docs.git
```

**From a checkout** — no install at all:

```sh
git clone https://github.com/dberardi2020/career-docs.git
cd career-docs
python3 -m venv .venv && .venv/bin/pip install -e .
python3 -m career_docs --help
```

Then scaffold somewhere to keep your resume:

```sh
career-docs init ~/CareerDocs   # the workspace, including the agent skills
cd ~/CareerDocs/Resume          # fill in resume.json, then:
career-docs lint
career-docs catalogue
```

### Hand it to your coding agent

Already inside Claude Code (or Cursor, or any coding agent)? Paste this and it will do the
setup for you:

```text
Install career-docs from https://github.com/dberardi2020/career-docs

- Preferred: `pipx install git+https://github.com/dberardi2020/career-docs.git`,
  which puts a `career-docs` command on my PATH. If pipx isn't available, clone the
  repo, make a venv, `pip install -e .`, and symlink `.venv/bin/career-docs` onto my
  PATH instead.
- Then run `career-docs init <where I keep my documents>` to scaffold a career
  workspace. That also installs the `career-resume-update` and `career-layouts-browse` skills into
  the workspace's .claude/skills/, which teach you the workflow and the rules — read them before
  touching my resume.
- Then help me fill in Resume/resume.json, run `career-docs lint`, and build me a
  catalogue of layouts to look at.

It needs Python 3.11+, and a Chromium-family browser for PDF export only. Tell me if
anything is missing.
```

## Driving it from your agent

The intended interface is not the CLI — it's your coding agent. `init` installs two
[Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills) into the workspace's
`.claude/skills/`, and your agent picks them up automatically. Either just say what you want and
the matching skill fires, or call it by name — both work:

| Skill | Say something like | It handles |
|---|---|---|
| **`career-resume-update`** | "update my summary", "lint my resume", "publish a PDF" | editing content, linting, publishing — and the anti-fabrication rule (it will not invent a metric) |
| **`career-layouts-browse`** | "show me some layouts", "try a different look", "make it one column" | browsing the design space, then publishing the one you pick |

You don't have to invoke them by name — describe the task and the right skill fires — but you can:
`/career-resume-update` and `/career-layouts-browse` are there when you want them. The skills carry
no personal data, so `career-docs init --skill-only` re-installs or refreshes them at any time.
Everything below
is the substrate they drive — documented so nothing is hidden, not so you type it.

## Commands

| Verb | What it does |
|---|---|
| `init [dir]` | Scaffold a workspace: `resume.json`, folders, working rules, and the agent skills (`career-resume-update` for content, `career-layouts-browse` for the look). `--skill-only` installs or refreshes just the skills in a folder you already have. |
| `lint` | Check the profile and a layout: parse safety, structure, vague or unquantified claims. |
| `catalogue` | Build a static, browsable folder of layouts. Opens from `file://`, no server, and still filters and pages the whole space in the browser. |
| `serve` | The same viewer with a process behind it — previews rendered on request, plus PDF export. |
| `publish --theme <spec>` | Write the deliverable (`.pdf`, `.html`, `.md`) beside the profile. |

The profile path is optional everywhere: commands walk up from the working directory looking
for `resume.json`, or read `CAREER_DOCS_RESUME`. `--theme` takes a preset (`default`,
`plain`, `editorial`, `warm`) or any spec name from the catalogue.

**Scratch renders never sit beside your source.** Catalogues and exports go to
`~/.cache/career-docs/`; only `publish` writes into the workspace, and only as the one
canonical deliverable — so the folder always answers "which file do I send?" instantly.

## On applicant tracking systems

Layout rules here are justified by **mechanism, never by magnitude**. Parsers demonstrably
extract text top-to-bottom and left-to-right, so a two-column layout genuinely scrambles
reading order. That is verifiable, it is sufficient, and it is why every generated layout is
single-column and ≥10pt *by construction* — a test re-extracts published PDFs and asserts the
text comes back in document order.

## Testing

QA runs in three layers — run the ones a change touches, ship when they're green:

- **Unit** — `pytest -q` (208 tests, ~30s): fast, mocked, property-based across the whole
  10,080-layout space. The CI gate.
- **Acceptance** — `python qa/acceptance.py`: the un-mockable surface as real processes — the
  installed CLI as a subprocess, a live `serve` server over real HTTP, a real headless-Chrome PDF,
  and the viewer's JavaScript asserted in a real browser. Non-zero exit on failure; skips cleanly
  when no browser is present. Runs standalone — no extra tooling.
- **Agentic browser pass** — the interactions and *looks-right* a harness can't assert, driven live
  against `serve`. The repo's testable surfaces, flows and gotchas live in
  [`qa/product-map.md`](qa/product-map.md).

Full approach, coverage and CI: [`docs/technical/testing.md`](docs/technical/testing.md).

## Roadmap

The design space, the viewer, the linter and publishing all work and are covered by tests.
These are not built yet:

- **Import** an existing resume (PDF/DOCX → profile) — the biggest gap, since today you
  transcribe once before anything works.
- **Grouping the grid by an axis** — filtering landed (every axis is a multi-select, driven
  from the header or by clicking a card's chip), but clustering the grid *by* an axis has not.
- **An inspector** — a live, read-only view of the profile as it is edited, showing what
  changed.
- **Provenance** — per claim, whether it is your asserted fact or model-generated prose.
- **Cover letters and applications**, from the same data model.

The backlog is [`docs/tickets/tickets.md`](docs/tickets/tickets.md).

## Documentation

Full docs live in [`docs/`](docs/README.md):

- **[Product](docs/product/README.md)** — the problem, the vocabulary, and how to use it, no code assumed.
- **[Technical](docs/technical/README.md)** — architecture, modules, data model, testing.
- **[Decisions](docs/decisions/README.md)** — the architecture decision records (*why* it's built this way).

[`llms.txt`](llms.txt) is the same orientation for an agent, without cloning.

## License

[MIT](LICENSE) © Dimitri Berardi
