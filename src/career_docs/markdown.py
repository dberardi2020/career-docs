"""Render a `Resume` back to Markdown.

Markdown used to be the source of truth here, and losing it outright would be a
real regression: it is the format that diffs cleanly, reads without a browser,
and shows up legibly in a chat window. So it survives as a *generated output*.

The distinction matters. Because it is generated, it can never drift from the
document that actually gets submitted — which is exactly the failure the old
hand-written `resume.html` had. Edit the JSON; the Markdown follows.
"""
from __future__ import annotations

from . import model
from .model import date_range


def _bullets(highlights) -> list[str]:
    return [f"- {h}" for h in (highlights or [])]


def render(resume) -> str:
    out: list[str] = [f"# {resume.name}", ""]

    contact = [resume.basics.get("phone"), resume.location]
    if line := " | ".join(str(c) for c in contact if c):
        out += [line]
    links = [resume.basics.get("email")]
    links += [p.get("url") for p in resume.profiles if p.get("url")]
    if line := " | ".join(str(link) for link in links if link):
        out += [line]
    out += [""]

    if resume.label:
        out += [f"**{resume.label}**", ""]
    if resume.summary:
        out += [resume.summary, ""]

    for group in resume.skills:
        keywords = group.get("keywords") or []
        if keywords:
            out += [f"**{group.get('name', '')}:** {', '.join(keywords)}", ""]

    if resume.work:
        out += ["---", "", "## Experience", ""]
        for entry in resume.work:
            head = " - ".join(p for p in (entry.get("position"), entry.get("name")) if p)
            meta = " | ".join(str(m) for m in (
                entry.get("location"),
                date_range(entry.get("startDate"), entry.get("endDate")),
            ) if m)
            out += [f"**{head}** - {meta}" if meta else f"**{head}**"]
            if note := entry.get("note"):
                out += [f"*{note}*"]
            out += [""] + _bullets(entry.get("highlights")) + [""]

            # Each title held at this employer, with the bullets earned under it.
            # Markdown has no layout axis, so this always reads the plainest way
            # that still says which work belongs to which title.
            for stint in model.stints(entry):
                when = date_range(stint.get("startDate"), stint.get("endDate"))
                title = stint.get("position", "")
                out += [f"*{title}* - {when}" if when else f"*{title}*", ""]
                out += _bullets(stint.get("highlights")) + [""]

    if resume.projects:
        out += ["---", "", "## Projects", ""]
        for entry in resume.projects:
            head = entry.get("name", "")
            if url := entry.get("url"):
                head += f" - {url}"
            out += [f"**{head}**"]
            if description := entry.get("description"):
                out += ["", description]
            out += [""] + _bullets(entry) + [""]

    if resume.education:
        out += ["---", "", "## Education", ""]
        for entry in resume.education:
            out += [f"**{entry.get('institution', '')}** - {entry.get('location', '')}".rstrip(" -")]
            study = " ".join(str(v) for v in (entry.get("studyType"), entry.get("area")) if v)
            meta = [study]
            if end := entry.get("endDate"):
                meta.append(f"Graduated {date_range(end, end).split(' - ')[0]}")
            if score := entry.get("score"):
                meta.append(f"GPA {score}")
            out += [", ".join(m for m in meta if m), ""]

    # Collapse runs of blank lines the section builders can leave behind.
    lines: list[str] = []
    for line in out:
        if line == "" and lines and lines[-1] == "":
            continue
        lines.append(line)
    return "\n".join(lines).rstrip() + "\n"
