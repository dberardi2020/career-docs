"""Check a resume against ATS and screening best practices.

This is the part that makes the pipeline a tool rather than a renderer. A resume
can be valid (`model.py` loads it) and still be quietly unsubmittable — buried in
a two-column layout, set in 8pt type, or carrying an objective statement that
screeners down-rank. Those failures are invisible in the source document and only
bite after a human or an ATS parser has already discarded you.

Rules encode the guidance in `resume-best-practices.md`. Each is deliberately
narrow and cites its reasoning, because a linter that cries wolf gets muted.

`ERROR`   likely to get the document mis-parsed or auto-rejected.
`WARNING` weakens the resume; a deliberate choice may override it.
`INFO`    worth a look, commonly intentional.

Stdlib only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from . import model

ERROR, WARNING, INFO = "ERROR", "WARNING", "INFO"

# Objective-style openers. Objective statements are obsolete and, worse, read as
# what the candidate wants rather than what they deliver.
_OBJECTIVE_RE = re.compile(
    r"^\s*(seeking|looking (to|for)|a motivated|aspiring|desire[sd]? to|"
    r"my goal is|to obtain|hoping to)\b",
    re.IGNORECASE,
)

_OBSOLETE_PHRASES = (
    "references available upon request",
    "references upon request",
)

# A street address is a privacy leak and adds nothing; city/state is the norm.
_STREET_RE = re.compile(r"\d+\s+[A-Za-z].*\b("
                        r"st|street|ave|avenue|rd|road|blvd|boulevard|ln|lane|"
                        r"dr|drive|ct|court|way|unit|apt|suite)\b\.?",
                        re.IGNORECASE)

_NUMBER_RE = re.compile(r"\d")

# Bullets that assert scope without measuring it. These are the ones most worth
# rewriting, so they get called out specifically rather than lumped together.
_VAGUE_SCOPE_RE = re.compile(
    r"\b(various|numerous|multiple|several|many|a number of|helped|assisted|"
    r"worked on|responsible for)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Finding:
    level: str
    rule: str
    message: str
    where: str = ""

    def __str__(self) -> str:
        loc = f" [{self.where}]" if self.where else ""
        return f"{self.level:<7} {self.rule}{loc}: {self.message}"


def _role_label(entry: dict, index: int) -> str:
    name = entry.get("name") or entry.get("organization") or f"work[{index}]"
    position = entry.get("position")
    return f"{position}, {name}" if position else str(name)


def check(resume, *, theme=None) -> list[Finding]:
    """Run every rule. `theme` is optional; layout rules are skipped without it."""
    out: list[Finding] = []
    out += _check_contact(resume)
    out += _check_summary(resume)
    out += _check_experience(resume)
    out += _check_skills(resume)
    out += _check_obsolete(resume)
    if theme is not None:
        out += _check_theme(theme)
    order = {ERROR: 0, WARNING: 1, INFO: 2}
    return sorted(out, key=lambda f: (order[f.level], f.rule))


def _check_contact(resume) -> list[Finding]:
    out = []
    basics = resume.basics
    location = basics.get("location", {})

    for value in (location.get("address"), basics.get("summary", "")):
        if value and _STREET_RE.search(str(value)):
            out.append(Finding(
                WARNING, "contact/street-address",
                "A full street address is obsolete and leaks your home address. "
                "City and state (or region) is the current norm.",
            ))
            break

    if not basics.get("email"):
        out.append(Finding(ERROR, "contact/email", "No email address."))
    if not basics.get("phone"):
        out.append(Finding(WARNING, "contact/phone", "No phone number."))

    networks = {p.get("network", "").lower() for p in resume.profiles}
    for expected in ("linkedin", "github"):
        if expected not in networks:
            out.append(Finding(
                WARNING, f"contact/{expected}",
                f"No {expected.title()} profile. Both are expected for engineering roles.",
            ))
    return out


def _check_summary(resume) -> list[Finding]:
    out = []
    summary = (resume.summary or "").strip()
    if not summary:
        out.append(Finding(
            INFO, "summary/missing",
            "No professional summary. Recommended at 5+ years — but only if "
            "specific; a generic one is worse than none.",
        ))
        return out

    if _OBJECTIVE_RE.match(summary):
        out.append(Finding(
            ERROR, "summary/objective",
            "This reads as an objective statement (what you want) rather than a "
            "summary (what you deliver). Objectives are obsolete and down-ranked.",
        ))

    words = len(summary.split())
    if words > 90:
        out.append(Finding(
            WARNING, "summary/length",
            f"{words} words. Target 2-3 headline-style sentences; long summaries "
            f"get skimmed past.",
        ))
    if not _NUMBER_RE.search(summary):
        out.append(Finding(
            INFO, "summary/unquantified",
            "No figure in the summary. A scope signal (years, team size, scale) "
            "is what separates it from a generic one.",
        ))
    return out


def _check_experience(resume) -> list[Finding]:
    out = []
    work = resume.work
    if not work:
        out.append(Finding(ERROR, "work/missing", "No work experience."))
        return out

    for i, entry in enumerate(work):
        label = _role_label(entry, i)
        highlights = model.highlights_of(entry)

        if not highlights:
            out.append(Finding(
                ERROR, "work/no-highlights",
                "No bullets — the role is a header with no evidence.", label,
            ))
            continue

        # Metrics matter most on the roles a screener actually reads: the
        # current one and the one before it.
        quantified = sum(1 for h in highlights if _NUMBER_RE.search(str(h)))
        if quantified == 0:
            level = ERROR if i < 2 else WARNING
            out.append(Finding(
                level, "work/unquantified",
                f"None of {len(highlights)} bullets contain a figure. A reader "
                f"cannot tell the scale of the work from the prose alone. "
                f"(Ask for the number — never invent one.)", label,
            ))
        elif quantified < len(highlights) / 3:
            out.append(Finding(
                INFO, "work/thin-metrics",
                f"Only {quantified} of {len(highlights)} bullets are quantified.",
                label,
            ))

        if i == 0 and len(highlights) < 4:
            out.append(Finding(
                WARNING, "work/thin-role",
                f"{len(highlights)} bullets on your most recent role. 5-10 is the "
                f"norm, and this is the role that gets read.", label,
            ))
        if len(highlights) > 10:
            out.append(Finding(
                INFO, "work/dense-role",
                f"{len(highlights)} bullets. Past ~10 the weakest ones dilute the "
                f"strongest.", label,
            ))

        for h in highlights:
            match = _VAGUE_SCOPE_RE.search(str(h))
            if match and not _NUMBER_RE.search(str(h)):
                out.append(Finding(
                    INFO, "work/vague-scope",
                    f"{match.group(0)!r} asserts scope without measuring it: "
                    f"{str(h)[:60]}...", label,
                ))
    return out


def _check_skills(resume) -> list[Finding]:
    out = []
    total = sum(len(group.get("keywords") or []) for group in resume.skills)
    if total == 0:
        out.append(Finding(WARNING, "skills/missing", "No skills listed."))
    elif total > 20:
        out.append(Finding(
            WARNING, "skills/bloat",
            f"{total} skills listed. 8-12 curated to the target role outperform a "
            f"long list — some screeners read length as lack of depth.",
        ))
    return out


def _check_obsolete(resume) -> list[Finding]:
    out = []
    blob = " ".join(str(v) for v in (resume.summary, resume.basics.get("label", ""))).lower()
    for phrase in _OBSOLETE_PHRASES:
        if phrase in blob:
            out.append(Finding(
                WARNING, "obsolete/phrase",
                f"{phrase!r} is obsolete filler — it is assumed.",
            ))
    return out


def _check_theme(theme) -> list[Finding]:
    """Layout rules. A theme declares these; see `themes/__init__.py`."""
    out = []
    if getattr(theme, "columns", 1) > 1:
        out.append(Finding(
            ERROR, "layout/multi-column",
            f"Theme {theme.name!r} is {theme.columns}-column. Parsers extract text "
            f"top-to-bottom, left-to-right, so a sidebar is read as a separate "
            f"block and interleaves with the main column - and the sidebar is "
            f"usually where skills and contact details live.",
        ))
    min_pt = getattr(theme, "min_font_pt", 10)
    if min_pt < 10:
        out.append(Finding(
            WARNING, "layout/small-type",
            f"Theme {theme.name!r} sets type as small as {min_pt}pt. 10pt is the "
            f"floor for reliable parsing and human readability.",
        ))
    if getattr(theme, "remote_assets", False):
        out.append(Finding(
            WARNING, "layout/remote-assets",
            f"Theme {theme.name!r} loads assets over the network. If the fetch "
            f"fails at render time the PDF silently reflows.",
        ))
    return out
