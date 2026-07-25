# Overview

What `career-docs` is, the problem it addresses, and the principles the rest of the
codebase follows. Read [`concepts.md`](concepts.md) next for the vocabulary.

## The idea, in one paragraph

Your resume is data, not a document — but the tools treat it as a document, so the file you
send drifts from the file you edit, and choosing how it *looks* means picking from a handful
of themes someone else designed. This keeps one structured **profile** as the only thing you
edit, generates a **space** of layouts from it, and lets you browse that space until
something looks right. The editing happens through a coding agent: you say what to change and
it changes the data. Publishing writes one **deliverable** — PDF, HTML and Markdown — from
the layout you chose.

Scope, stated plainly: **the resume is the part that is built.** The workspace `init`
scaffolds also holds cover letters and applications, and the name points at bringing them
under the same treatment — but nothing in these docs describes a capability that does not
exist today.

## Who it is for

Someone who already works inside a coding agent, keeps their resume under version control or
wishes they did, and is tired of a `.docx` that is simultaneously the source and the output.

It is **not** for someone who wants a web form and a template gallery. That is well served,
and running a server to edit a text file is the wrong shape. See
[`decisions/0007-keep-the-in-house-renderer.md`](../decisions/0007-keep-the-in-house-renderer.md)
for what was evaluated and rejected.

## What is actually different

Three things, none of which existed elsewhere when this was surveyed in July 2026:

| | |
|---|---|
| **Layouts as a design space** | Not a theme list. Seven independent axes, multiplied out, enumerated exhaustively and browsed with the axes as facets. |
| **A linter for the *layout*** | Plenty of tools check your prose. Nothing open-source checks whether the layout itself survives a parser. Every generated layout is single-column and ≥10pt *by construction*, and a test re-extracts published PDFs to prove text comes back in document order. |
| **Built for an agent to drive** | The CLI is the substrate. The workflow, the rules, and the guardrails ship as a skill that installs into the workspace, so the agent knows them without being briefed. |

**What it is not:** another resume generator. That category is mature and mostly abandoned —
the surveyed tools have download counts in the hundreds. Building a better renderer was never
the point.

## Design principles

These are load-bearing. Where a feature and a principle disagree, the principle wins.

**Agent-first, not agent-optional.** The command line is what the agent drives. A workflow
that requires a human to memorise commands has failed. If a turn would end by telling someone
to run something, run it.

**Data in one place.** One profile, edited once, rendered many ways. No format is
authoritative except the profile, and generated files are never hand-edited.

**Enumerate rather than recommend.** The space is finite, deterministic and categorical, so
facets answer everything a recommender would — with no sampler, no seed, and no session
state. See [`decisions/0002-browse-not-search.md`](../decisions/0002-browse-not-search.md).

**Generated files are disposable** and never sit beside source. Scratch goes to a cache; only
publishing writes into the workspace, as one canonical deliverable, so the folder always
answers "which file do I send?"

**The tool is public; the content never is.** Every feature must be describable without
reference to any particular person's resume. The tool holds no content; the workspace holds
no code.

**Never invent a career fact.** The tooling actively creates pressure to break this — the
linter flags unquantified bullets, and the obvious way to satisfy a linter is to supply a
number. So the linter only ever reports. See
[`decisions/0006-the-linter-reports-it-never-edits.md`](../decisions/0006-the-linter-reports-it-never-edits.md).

**Explainable in one page**, or out of scope.

## On applicant tracking systems

Layout rules here are justified by **mechanism, never by magnitude**. Parsers demonstrably
extract text top-to-bottom and left-to-right, so a two-column layout genuinely scrambles
reading order. That is verifiable and sufficient.

You will not find a rejection statistic anywhere in this project. The ubiquitous "75% of
resumes never reach a human" traces to a vendor that folded in 2013 without ever publishing a
study, and the skeptical counter-numbers are vendor-produced too. Nobody has good public
data, so nothing here rests on any.

## Where things live

The tool holds no content. The workspace holds no code. That split is what lets the tool be
published while a resume stays private.

```
career-docs/                 a workspace/
  the tool. generic.               the content. private.
  ─────────────────                ──────────────────────
  render / lint / browse           profile   (the data you edit)
  the axes and the space           renders   (the current deliverable)
  the packaged skill        ──▶    archive   (pre-edit snapshots)
  the workspace template           letters, applications
```

Three artefacts, deliberately distinct — conflating them is the failure mode this section
exists to prevent:

1. **The tool** — generic, public, zero personal content.
2. **The workspace template** `init` scaffolds — generic; a starting point, not anyone's
   actual resume.
3. **Someone's workspace** — personal, private, never in this repo.
