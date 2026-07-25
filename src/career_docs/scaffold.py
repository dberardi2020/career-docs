"""Scaffold a career workspace.

The tool renders resumes; it does not, on its own, tell you how to *work*. Anyone
who clones this is left holding a CLI and the question "so where do I put my
resume, and what happens when I want to tailor it for a job?" That answer is a
folder layout and a couple of rules, which is exactly the kind of thing that
should ship rather than be re-derived.

So `init` writes a workspace: somewhere for the resume, somewhere for cover
letters, somewhere for per-application artefacts, a `CLAUDE.md` carrying the rules
that matter, and a Claude Code skill so an agent picks all of it up without being
briefed.

Nothing here is required to use the CLI. It is the opinionated default for people
who want one.
"""
from __future__ import annotations

from pathlib import Path

STARTER_RESUME = """{
  "$schema": "https://raw.githubusercontent.com/jsonresume/resume-schema/master/schema.json",
  "basics": {
    "name": "Your Name",
    "label": "Software Engineer | Your specialisms here",
    "email": "you@example.com",
    "phone": "(555) 555-5555",
    "location": { "city": "Your City", "region": "ST", "countryCode": "US" },
    "profiles": [
      { "network": "LinkedIn", "username": "you", "url": "https://www.linkedin.com/in/you" },
      { "network": "GitHub", "username": "you", "url": "https://github.com/you" }
    ],
    "summary": "Two or three headline sentences. Name a role, a specialism, and a scope signal. A generic summary is worse than none."
  },
  "skills": [
    { "name": "Languages", "keywords": ["..."] },
    { "name": "Frameworks & Libraries", "keywords": ["..."] },
    { "name": "Tools", "keywords": ["..."] }
  ],
  "work": [
    {
      "name": "Employer",
      "position": "Your Title",
      "location": "City, ST (Remote)",
      "startDate": "2024-01",
      "highlights": [
        "What you built, what it was built with, and what it was for."
      ]
    }
  ],
  "education": [
    {
      "institution": "Your University",
      "location": "City, ST",
      "studyType": "Bachelor of Science",
      "area": "in Computer Science",
      "endDate": "2020-12"
    }
  ]
}
"""

WORKSPACE_CLAUDE_MD = """# Career workspace

The live workspace for career work: the resume, cover letters, and job applications.
Scaffolded by `career-docs init`.

This is a workspace, not an archive of records. Keep signed offer letters, payslips and
similar somewhere else — this folder is for things actively being worked.

## Layout

```
Resume/          resume.json (source of truth) + the published deliverable + Archive/
Cover Letters/   drafts and sent letters
Applications/    per-posting: the job posting + the tailored resume + the letter
Reference/       notes worth consulting while writing
```

## The anti-fabrication rule — read this before editing any resume content

**Never invent a fact about this person's career. Not a metric, not a date, not a scope
claim, not a technology they did not use.**

This rule exists because the tooling actively creates pressure to break it. The linter
flags bullets that contain no figures. The obvious way to satisfy the linter is to supply
a figure. **Supplying it is not your job.** A resume is a factual representation made to
employers; an invented "reduced p99 latency by 40%" is a misrepresentation they would have
to defend in an interview and cannot.

In practice:

- **Flagging** that a bullet lacks a number is useful. **Filling it in is not.**
- If a metric would strengthen a bullet, **ask**, and leave it unquantified until answered.
- Rewriting *their* facts into stronger prose is fine and encouraged. Introducing *new*
  facts is not.
- If unsure whether something is their claim or your inference, treat it as yours and ask.
- Never fill a gap with a plausible placeholder that reads like a real figure.

The line is not "AI helped write this" — that is normal and fine. The line is
**misrepresentation**, and invented metrics are the specific failure mode.

## Editing

`Resume/resume.json` is the source of truth. Everything else is generated — never hand-edit
a `.html`, `.md`, or `.pdf`, because the next publish overwrites it and the two then
disagree silently.

**Never delete a skill from the data.** A skills list is built over years. Curating which
skills appear in a given variant is a rendering choice, not a deletion.

Archive before a substantive rewrite. `Archive/` uses one scheme, `YYYYMMDD-description.ext`,
so it sorts chronologically:

```
cp Resume/resume.json "Resume/Archive/$(date +%Y%m%d)-pre-<change>.json"
```

## Commands

You should rarely need these — ask your agent instead; it has the `career-*` skills. They
are here so nothing is hidden.

```
career-docs lint                       # ATS + content checks
career-docs catalogue                  # build a browsable page of layout options
career-docs serve                      # the same viewer, with PDF export
career-docs publish --theme default    # write the deliverable beside resume.json
```

Paths are optional — commands walk up from the working directory to find `resume.json`.
Scratch renders go to `~/.cache/career-docs/`; only `publish` and `catalogue` write here.

**Never create a virtualenv inside this folder** if it is file-synced (Dropbox, iCloud,
Drive, a NAS). Virtualenvs carry absolute paths and per-machine binaries.
"""

SKILL_RESUME_UPDATE_MD = """---
name: career-resume-update
description: Update the user's resume content — edit, lint, and publish it. Use whenever the request is to change, rewrite, regenerate, lint, or export/publish their resume. Handles "update my resume", "rewrite my summary", "lint my resume", "publish a PDF". For choosing or changing the layout/design/theme, use the `career-layouts-browse` skill. (Named with the `career-` prefix, not `resume`, because `/resume` is a built-in Claude Code command.)
---

# Career — resume update

The resume lives at `Resume/resume.json` ([JSON Resume](https://jsonresume.org/schema)).
Everything beside it is **generated** — never hand-edit a `.md`, `.html`, or `.pdf`, because
the next publish silently overwrites it.

The tool is `career-docs`. It finds `resume.json` by walking up from the working
directory, so the path argument is optional. **You run these, not the user** — they work in an
agent session; if a turn would end by telling them to run a command, run it instead.

## Commands

```bash
career-docs lint                       # ATS + content checks
career-docs publish                    # (re)write the deliverable beside resume.json
```

`publish` overwrites the canonical deliverable beside `resume.json` — that *is* the file
attached to an application. It snapshots the previous one into `Archive/` first, so a publish
never destroys the last version.

**Publish remembers the layout and formats.** A bare `publish` re-renders the layout and
formats last used (recorded in `.career-docs.json`), so after a content edit you do **not**
re-pick the design. Change them only when asked — `--theme <preset|layout-id>` or
`--formats <subset of pdf,html,md>`. To browse and choose a layout, use the
`career-layouts-browse` skill.

## Before editing content — the rule that overrides everything

**Read `CLAUDE.md` in the workspace root and follow its anti-fabrication rule.** Never invent
a fact about their career: no metric, no date, no scope claim, no technology they did not use.

The linter will flag unquantified bullets. **Do not resolve that by supplying a number.**
Flagging the gap is useful; filling it is misrepresentation they would have to defend in an
interview.

You may rewrite their facts into stronger prose, restore text from `Resume/Archive/`, and
compute figures that follow arithmetically from dates already in the data. Nothing else.

Also: **never delete a skill from `resume.json`.** Per-variant curation is a rendering
choice, not a deletion.

## Workflow for a content change

1. Archive first — `Archive/` uses `YYYYMMDD-description.ext`, describing what the snapshot
   is *before*: `cp Resume/resume.json "Resume/Archive/$(date +%Y%m%d)-pre-<change>.json"`
2. Edit `resume.json` only.
3. `career-docs lint` — compare against the pre-edit baseline; never silence a finding
   with invented data.
4. `career-docs publish` — keeps the layout and formats already chosen.
5. Report what changed, and list anything you needed but did not have.
"""

SKILL_LAYOUTS_BROWSE_MD = """---
name: career-layouts-browse
description: Browse the space of resume layouts and choose one to publish. Use when the request is about the resume's look — its layout, design, theme, colour, or output format — e.g. "show me layouts", "change my resume's design", "try a different look", "make it one column", "pick a layout". For editing resume content, use the `career-resume-update` skill.
---

# Career — layouts browse

A layout is not a template: it is one point in a design space of thousands, built from seven
independent choices (palette, typeface, header, skills, promotion, density, grouping) over one
renderer. Browsing that space and publishing the one the user picks is what this skill does;
editing resume *content* is the `career-resume-update` skill.

The tool is `career-docs`, run from the resume folder (it walks up to find `resume.json`).
**You run these, not the user.**

## Commands

```bash
career-docs serve                      # interactive viewer: browse, filter, page, publish
career-docs catalogue                  # the same browser, as a static folder
```

`serve` opens the viewer **in the user's own browser** — it calls their default browser for
them — and then blocks until ctrl-c, so **run it in the background** and let their browser open on
its own. It shows a grid of live renders of the user's *own* resume in different layouts, with
paging and shuffle to move through the space, and a filter for **every** axis — colour swatches
plus a dropdown per remaining choice. Several values on one axis mean *any of these*; axes
combine to narrow further; clicking a chip on a card filters to that value.

`catalogue` is the same page written to a folder, so it needs no process and survives being
committed or sent to someone. It browses and filters the whole space too — the difference is
that only `serve` can **Export PDF** or **Make this my resume**, because those need a backend.

**This viewer is for the user to look at, not for you to drive.** Do **not** open or navigate it
with browser automation (Claude for Chrome / a Claude-controlled tab) — just start `serve` and their
browser opens by itself. The user browses and reacts in words; your job is to publish the layout
they pick (below). *(Driving `serve` yourself is a QA activity — a different, dev-only skill — never
this one.)*

## Choosing a layout

- The user reacts to what they see and says it in words — "the serif one", "the moss one",
  "number 7". Resolve that to a layout, then publish it; don't make them copy an id.
- Publish the choice: `career-docs publish --theme <layout-id>` (or a preset —
  `default`, `plain`, `editorial`, `warm`). That overwrites the deliverable, snapshots the
  previous design to `Archive/` first, and records the layout so later content edits keep it.
- In the viewer, **Make this my resume** publishes the layout on screen directly.
- `--formats <subset of pdf,html,md>` narrows which files are written (all three by default).

Changing the layout does not touch content — but publishing still writes the file an employer
sees, so the anti-fabrication rule in the workspace `CLAUDE.md` still governs: never introduce
a claim that is not the user's.
"""

WORKSPACE_README = """# Career workspace

Scaffolded by [`career-docs`](https://github.com/dberardi2020/career-docs) —
`career-docs init`.

## Start here

1. Fill in `Resume/resume.json`. Already have a resume? See the import notes in the tool's
   README — until then, transcribe it once; everything downstream is generated from it.
2. `cd Resume && career-docs lint` — see what a parser and a screener would object to.
3. `career-docs catalogue` — build a page of layout options and open it.
4. `career-docs publish --theme <id>` — writes the file you actually send.

Better still, ask your coding agent for any of the above — `init` installs the
`career-resume-update` and `career-layouts-browse` skills that teach it the workflow and the rules.

## What goes where

| Folder | For |
|---|---|
| `Resume/` | `resume.json` (the only authored file), the published deliverable, and dated snapshots in `Archive/` |
| `Cover Letters/` | Drafts and sent letters |
| `Applications/` | One folder per posting: the job description, the tailored resume, the letter |
| `Reference/` | Notes worth consulting while writing |

`CLAUDE.md` holds the working rules, including the anti-fabrication rule — read it before
letting any agent edit your resume.
"""

# The skills are generic — they carry no personal data — so refreshing them to
# the current shipped version is always safe. Personal context belongs in the
# workspace `CLAUDE.md`, never in a skill.
SKILLS = {"career-resume-update": SKILL_RESUME_UPDATE_MD,
          "career-layouts-browse": SKILL_LAYOUTS_BROWSE_MD}


def _write(path: Path, content: str, *, force: bool = False) -> str:
    if path.exists() and not force:
        return f"  skip  {path}  (exists)"
    existed = path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"  {'update' if existed else 'write '} {path}"


def _write_skills(root: Path, *, force: bool) -> list[str]:
    return [_write(root / ".claude" / "skills" / name / "SKILL.md", md, force=force)
            for name, md in SKILLS.items()]


def init(root: Path, *, skill_only: bool = False) -> list[str]:
    """Create the workspace. Never overwrites an existing file — except that
    `skill_only` refreshes the skills in place, since they carry no user data and
    `init --skill-only` is how a workspace re-syncs them to the current version."""
    if skill_only:
        return _write_skills(root, force=True)

    out: list[str] = []
    out.append(_write(root / "CLAUDE.md", WORKSPACE_CLAUDE_MD))
    out.append(_write(root / "README.md", WORKSPACE_README))
    out.extend(_write_skills(root, force=False))
    out.append(_write(root / "Resume" / "resume.json", STARTER_RESUME))
    for folder in ("Resume/Archive", "Cover Letters", "Applications", "Reference"):
        target = root / folder
        target.mkdir(parents=True, exist_ok=True)
        # Empty directories do not survive git, and these are meaningful structure.
        keep = target / ".gitkeep"
        if not any(target.iterdir()):
            keep.write_text("", encoding="utf-8")
            out.append(f"  write {target}/")
    return out
