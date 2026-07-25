# Module reference

What each module is responsible for, and the parts of its surface worth knowing. Roughly
bottom-up: the data, then the space, then the renderers, then the surfaces.

`src/career_docs/`, 2,400 lines, stdlib only.

| Module | Lines | Responsibility |
|---|---|---|
| [`model.py`](#modelpy) | 265 | Load and validate a profile; normalise its shape |
| [`compose.py`](#composepy) | 508 | The axes, the `Spec`, the CSS, and HTML rendering |
| [`space.py`](#spacepy) | 138 | Enumerate, measure and name the design space |
| [`markdown.py`](#markdownpy) | 94 | Render a profile to Markdown |
| [`pdf.py`](#pdfpy) | 92 | Find a browser; drive it headless to make a PDF |
| [`lint.py`](#lintpy) | 262 | Check a profile and a layout; report findings |
| [`viewer.py`](#viewerpy) | 292 | The one viewer page |
| [`catalogue.py`](#cataloguepy) | 37 | Static delivery of the viewer |
| [`server.py`](#serverpy) | 145 | Served delivery of the viewer |
| [`deliverable.py`](#deliverablepy) | 63 | Write the published trio |
| [`scaffold.py`](#scaffoldpy) | 255 | The workspace `init` creates, and the agent skill |
| [`cli.py`](#clipy) | 245 | Argument parsing and command wiring |

---

## `model.py`

Owns the profile. `load(path)` reads JSON, validates, and returns a `Resume` — a frozen-ish
wrapper exposing sections (`basics`, `work`, `skills`, `education`, …) through properties that
return `[]` rather than raising, since JSON Resume marks everything but `basics` optional.

Validation **raises `ResumeError` on anything unrenderable** (bad types, malformed dates, a
role ending before it starts) and returns **notes** for things that are merely suspicious —
an unknown top-level section is reported rather than silently ignored, so a typo like
`experience` for `work` surfaces instead of rendering an empty resume.

Two helpers exist so callers do not each re-derive the same thing:

- `stints(entry)` — the title history within one employer, newest first, normalising the
  older `promotions` field into the newer `stints` shape. Returns `[]` when there is no
  progression.
- `highlights_of(entry)` — every bullet in a role, employer-level and per-stint, for callers
  that count bullets rather than place them.

`date_range(start, end)` produces the human string used by every renderer.

## `compose.py`

The largest module, and the only one that knows HTML.

**The axes** are module-level lists — `PALETTES`, `TYPEFACES`, `HEADERS`, `SKILLS`, `PROMOS`,
`DENSITIES`, `GROUPINGS`. Adding a value here grows the space; nothing else needs touching.

**`Spec`** is a frozen dataclass of seven categorical values, with `name` (the stable written-
out id) and `description` (the human phrase) as properties. `all_specs()` enumerates the
product; `PRESETS` names four of them.

**`css(spec)`** builds the stylesheet, including the print/screen margin rules described in
[`architecture.md`](architecture.md#print-versus-screen). **`render(resume, spec)`** assembles
the document: header, summary, skills, work, education. Section renderers are private and
take `(entity, spec)`.

**`as_theme(spec)`** wraps a spec as a `Theme` — a name, a render callable, and the
parse-safety claims the linter checks against (`columns`, `min_font_pt`, `remote_assets`,
`ats_safe`). Everything generated is single-column and ≥10pt, so those are constant today;
they stay declared because imported or hand-written layouts would not have that guarantee.

**All content routes through `esc()`.** No exceptions.

## `space.py`

The space as pure data. Knows nothing about rendering.

- `AXES` — `(attribute, values)` pairs, in stable order. `TOTAL` is their product.
- `distance(a, b)` — Hamming: the number of axes on which two specs disagree, 0–7.
- `neighbours(spec, radius)` — every spec within *radius* axis-changes.
- `spread(count)` — `count` layouts spread across the space by greedy farthest-point
  selection, deterministic, no seed. Tracks each candidate's distance to the chosen set
  incrementally; doing it naively is cubic in the size of the space and does not finish. Used
  by the static catalogue, where a small representative sample is the point.
- `browse_order()` / `page(i, n)` / `pages(n)` — the served viewer's paging. Every spec sorted
  once by a hash of its name (so a page is well-mixed rather than seven shades of one design),
  then sliced. Deterministic and wrapping: page *i* is the same layouts on every machine.
- `parse(name)` — decode a name back to a `Spec`, or `None`. A lookup per segment, not a scan.

## `markdown.py`

A profile as Markdown. Generated output, never a source — it exists because Markdown diffs
cleanly, reads without a browser, and pastes into a chat window. Preserves content, not
layout.

## `pdf.py`

`find_browser()` resolves a Chromium-family executable — `CAREER_DOCS_CHROME` first, then
known macOS and Windows paths, then `PATH` names on Linux — and raises `BrowserNotFound` with
an actionable message. `write(html, out_path)` drives it headless to print to PDF.

The only external dependency in the project, and the only reason a browser is required at all.

## `lint.py`

`check(resume, theme=None)` returns a list of `Finding(level, rule, message, where)`. Layout
rules are skipped when no theme is given. **It never mutates the profile** — see
[`../decisions/0006-the-linter-reports-it-never-edits.md`](../decisions/0006-the-linter-reports-it-never-edits.md).

| Group | Rules |
|---|---|
| `contact/` | `email` `phone` `street-address` |
| `summary/` | `missing` `objective` `length` `unquantified` |
| `work/` | `missing` `no-highlights` `unquantified` `thin-metrics` `thin-role` `dense-role` `vague-scope` |
| `skills/` | `missing` `bloat` |
| `obsolete/` | `phrase` |
| `layout/` | `multi-column` `small-type` `remote-assets` |

Severities: `ERROR` likely to be mis-parsed or auto-rejected · `WARNING` weakens the resume ·
`INFO` worth a look. Rules are narrow and cite their reasoning deliberately — a linter that
cries wolf gets muted.

## `viewer.py`

The one viewer page, as a single self-contained HTML string with a handful of substitutions.
No template engine, no dependencies, and it must work equally from `file://` and from the
server.

`page(specs, resume, *, preview, exportable)` is the entry point. `describe(spec)` is the
per-spec payload embedded as JSON — name, description, and axis values — and is also what
`options.json` carries, so an agent reads the same structure the page does.

`preview="file"` points at sibling `<name>.html`; `preview="route"` points at
`/preview/<name>`. `exportable` reveals the actions only a server can honour.

**Colour and typeface** are surfaced specially. Palette and typeface are the two axes the eye
reacts to first, so the served viewer gives each its own bar — a colour-swatch row and a
typeface-sample row. Holding one **filters** the browse to that subset: `/api/page` takes the
held axes as query params and returns only matching specs, so the layout count and page total
follow the hold (`space.page`/`pages`/`total` take an optional `filters` dict). The two holds
compose and appear in the detail view too. Disabled for the static catalogue, whose preview
files exist only for the specs it shipped.

## `catalogue.py`

Static delivery. Renders `count` layouts, writes the viewer as `index.html` beside them, plus
`options.json` for an agent. Self-contained and `file://`-browsable — no server, no build
step. 37 lines, because the viewer does the work.

## `server.py`

Served delivery. A stdlib `ThreadingHTTPServer` on loopback with four routes:

| Route | Does |
|---|---|
| `GET /` | The viewer, in route mode, exportable |
| `GET /api/page?i=<n>` | One page of specs as JSON; wraps, so any index is valid |
| `GET /preview/<name>` | Render one spec on request; 404 on an unparseable name |
| `POST /api/export` | Write a scratch PDF into the cache |
| `POST /api/publish` | Write the deliverable beside the profile |

The context dict is built at startup and holds no session. The **profile** is re-read per
request on an mtime change, since an agent edits it while the viewer watches.

## `deliverable.py`

Writing the deliverable, extracted so the command and the viewer cannot diverge.
`write(resume, spec, out_dir, stem, formats)` renders and writes the chosen `formats` (a subset
of `pdf, html, md`; all three by default); PDF goes last because it is the step that can fail.

Publishing records two choices in a hidden `.career-docs.json` sidecar so a bare re-publish
after a content edit repeats them (ADR-0009): `write_prefs`/`read_prefs` persist and read it,
and `recorded_layout(out_dir)` / `recorded_formats(out_dir)` return the last chosen layout id and
format set, or None to fall back.

`archive_existing(out_dir)` runs before each overwrite, copying the current deliverable (and its
sidecar) into `Archive/<timestamp>/` so a publish never destroys the previous design (ADR-0010);
it only ever adds folders, never touching what is already in `Archive/`.

`existing_stem(out_dir)` finds the deliverable already present so publishing **reuses that name**
instead of introducing a second convention — otherwise publishing duplicates a deliverable rather
than replacing it. "Present" means the recorded formats are all there (all three if none
recorded), so a PDF-only deliverable still matches; ambiguous cases fall back to `default_stem()`.

## `scaffold.py`

Everything `init` writes, as module-level strings: the starter profile, the workspace
`CLAUDE.md`, a `README.md`, and two agent skills — `SKILL_RESUME_UPDATE_MD`
(`career-resume-update`, resume content) and `SKILL_LAYOUTS_BROWSE_MD` (`career-layouts-browse`,
browsing the layout space), split by intent (ADR-0011). A full `init` never
overwrites an existing file and reports what it skipped; `init --skill-only` force-writes the
skills, since they carry no personal data and that command is how a workspace re-syncs them.

**This module is shipped content**, so it is held to the same bar as the README: no personal
details, no assumptions about the reader, and every command it documents must exist. Tests parse
this prose — both skills and the workspace `CLAUDE.md` — and assert both.

## `cli.py`

Argument parsing and wiring. Five commands: `init`, `lint`, `catalogue`, `serve`, `publish`.

| Helper | Does |
|---|---|
| `find_resume(explicit)` | Explicit path → `CAREER_DOCS_RESUME` → nearest `resume.json` walking up. Exits with guidance if none. |
| `cache_dir(path)` | `~/.cache/career-docs/<workspace>` — where everything generated goes. |
| `resolve_spec(name)` | Preset or spec name → `Spec`; exits listing the presets otherwise. |
| `resolve_layout(name)` | The same, as a `Theme`. |

Exit codes: `0` success · `1` lint errors, or a failed PDF · `2` an unloadable profile.

**This is the substrate, not the interface.** A human should not have to remember any of it.
