"""Load and validate a JSON Resume document.

The data layer. Everything downstream — themes, Markdown, PDF, lint — reads a
`Resume` and never touches raw JSON. Deliberately a *thin* wrapper: the schema is
JSON Resume (https://jsonresume.org/schema), not a bespoke shape, so the same
document stays portable to any other tool that speaks the standard.

Validation is structural, not stylistic. It answers "can this be rendered?" —
missing required fields, wrong types, malformed dates. Whether the *content* is
any good is `lint.py`'s job, and the two are kept apart on purpose: an agent
rewriting bullets should trip lint warnings, never a load error.

Stdlib only.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# JSON Resume date fields are ISO 8601, and may be truncated to year or
# year-month. `work[].endDate` is absent/empty for a current role.
_DATE_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")

_MONTHS = ("January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December")


class ResumeError(ValueError):
    """A resume document that cannot be rendered."""


def _human_date(value: str | None, *, present: str = "Present") -> str:
    """`2024-12` -> `December 2024`. Empty/absent -> `present`."""
    if not value:
        return present
    parts = value.split("-")
    year = parts[0]
    if len(parts) == 1:
        return year
    return f"{_MONTHS[int(parts[1]) - 1]} {year}"


def date_range(start: str | None, end: str | None) -> str:
    """The `December 2024 - Present` string themes render for a role."""
    return f"{_human_date(start)} - {_human_date(end)}"


@dataclass
class Resume:
    """A validated JSON Resume document."""

    data: dict
    source: Path | None = None
    # Non-fatal structural notes surfaced by the CLI (e.g. unknown sections).
    notes: list[str] = field(default_factory=list)

    # -- section accessors ------------------------------------------------
    # Themes read through these so a missing optional section renders as empty
    # rather than raising. JSON Resume marks every section but `basics` optional.

    @property
    def basics(self) -> dict:
        return self.data.get("basics", {})

    @property
    def name(self) -> str:
        return self.basics.get("name", "")

    @property
    def label(self) -> str:
        """The positioning line, e.g. `Backend Software Engineer`."""
        return self.basics.get("label", "")

    @property
    def summary(self) -> str:
        return self.basics.get("summary", "")

    @property
    def location(self) -> str:
        loc = self.basics.get("location", {})
        parts = [loc.get("city"), loc.get("region")]
        return ", ".join(p for p in parts if p)

    @property
    def profiles(self) -> list[dict]:
        return self.basics.get("profiles", [])

    def section(self, name: str) -> list[dict]:
        value = self.data.get(name, [])
        return value if isinstance(value, list) else []

    @property
    def work(self) -> list[dict]:
        return self.section("work")

    @property
    def education(self) -> list[dict]:
        return self.section("education")

    @property
    def projects(self) -> list[dict]:
        return self.section("projects")

    @property
    def skills(self) -> list[dict]:
        return self.section("skills")


# JSON Resume's top-level sections. Anything else is passed through untouched
# but reported, so a typo like `experience` (correct name: `work`) surfaces
# instead of silently rendering an empty resume.
def stints(entry: dict) -> list[dict]:
    """The title history within one employer, newest first.

    A promotion is not decoration — the bullets a person wrote as a senior
    engineer are different evidence from the ones they wrote a level below, and
    a resume that cannot say which is which loses the progression it is trying
    to show. So a `work` entry may carry `stints`, each with its own position,
    dates and highlights.

    The older `promotions` field held prior *titles* but no bullets, so it could
    never express that split. It is normalised into stints here — one synthesised
    stint for the current title, then the prior ones — so existing documents keep
    rendering and every caller sees a single shape.

    Returns `[]` for a role with no progression; callers render those flat.
    """
    raw = entry.get("stints")
    if isinstance(raw, list) and raw:
        return [s for s in raw if isinstance(s, dict)]

    prior = [p for p in (entry.get("promotions") or []) if isinstance(p, dict)]
    if not prior:
        return []

    prior = sorted(prior, key=lambda p: str(p.get("startDate") or ""), reverse=True)
    # The current title began when the most recent prior one ended.
    current = {
        "position": entry.get("position", ""),
        "startDate": prior[0].get("endDate") or entry.get("startDate"),
        "endDate": entry.get("endDate"),
    }
    return [current, *prior]


def highlights_of(entry: dict) -> list:
    """Every bullet in a work entry — employer-level first, then each stint's.

    Linting and Markdown care how many bullets a role has and whether they carry
    figures, not which title they sit under, so they read through this.
    """
    out = list(entry.get("highlights") or [])
    for stint in stints(entry):
        out += list(stint.get("highlights") or [])
    return out


KNOWN_SECTIONS = {
    "basics", "work", "volunteer", "education", "awards", "certificates",
    "publications", "skills", "languages", "interests", "references",
    "projects", "meta",
    # Editors use this for schema autocompletion; it is not a content section.
    "$schema",
}

# Sections whose entries carry dates we validate and render.
_DATED_SECTIONS = ("work", "volunteer", "education", "projects", "awards",
                   "certificates", "publications")


def _validate(data: dict) -> list[str]:
    """Return non-fatal notes; raise ResumeError on anything unrenderable."""
    if not isinstance(data, dict):
        raise ResumeError("Top level must be a JSON object.")

    basics = data.get("basics")
    if not isinstance(basics, dict) or not basics.get("name"):
        raise ResumeError("`basics.name` is required.")

    notes: list[str] = []
    for unknown in sorted(set(data) - KNOWN_SECTIONS):
        # A leading `_` (or `$`) is the near-universal "not data, ignore me"
        # convention — `_comment`, `$schema`. Warning on those is noise, not help.
        if unknown[:1] in ("_", "$"):
            continue
        notes.append(
            f"Unknown top-level section {unknown!r} — not part of JSON Resume, "
            f"so no theme will render it."
        )

    for name in _DATED_SECTIONS:
        entries = data.get(name, [])
        if not isinstance(entries, list):
            raise ResumeError(f"`{name}` must be an array.")
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ResumeError(f"`{name}[{i}]` must be an object.")
            for key in ("startDate", "endDate"):
                value = entry.get(key)
                if value and not _DATE_RE.match(str(value)):
                    raise ResumeError(
                        f"`{name}[{i}].{key}` is {value!r} — expected ISO 8601 "
                        f"(YYYY, YYYY-MM, or YYYY-MM-DD)."
                    )
            # A role that ends before it starts is almost always a bad agent edit.
            start, end = entry.get("startDate"), entry.get("endDate")
            if start and end and str(end) < str(start):
                raise ResumeError(
                    f"`{name}[{i}]` ends ({end}) before it starts ({start})."
                )
            highlights = entry.get("highlights")
            if highlights is not None and not isinstance(highlights, list):
                raise ResumeError(f"`{name}[{i}].highlights` must be an array.")

    _validate_stints(data.get("work", []))
    return notes


def _validate_stints(work: list) -> None:
    """`work[].stints` — the title history. A local extension; see `stints()`."""
    for i, entry in enumerate(work):
        raw = entry.get("stints")
        if raw is None:
            continue
        where = f"`work[{i}].stints`"
        if not isinstance(raw, list):
            raise ResumeError(f"{where} must be an array.")
        for j, stint in enumerate(raw):
            at = f"`work[{i}].stints[{j}]`"
            if not isinstance(stint, dict):
                raise ResumeError(f"{at} must be an object.")
            if not stint.get("position"):
                raise ResumeError(
                    f"{at}.position is required — a stint is a title you held."
                )
            for key in ("startDate", "endDate"):
                value = stint.get(key)
                if value and not _DATE_RE.match(str(value)):
                    raise ResumeError(
                        f"{at}.{key} is {value!r} — expected ISO 8601 "
                        f"(YYYY, YYYY-MM, or YYYY-MM-DD)."
                    )
            start, end = stint.get("startDate"), stint.get("endDate")
            if start and end and str(end) < str(start):
                raise ResumeError(f"{at} ends ({end}) before it starts ({start}).")
            bullets = stint.get("highlights")
            if bullets is not None and not isinstance(bullets, list):
                raise ResumeError(f"{at}.highlights must be an array.")
        if raw and entry.get("promotions"):
            raise ResumeError(
                f"`work[{i}]` has both `stints` and the older `promotions`. "
                f"Keep `stints` — it supersedes it."
            )


def load(path: str | Path) -> Resume:
    """Read and validate a JSON Resume file."""
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ResumeError(f"No such resume: {path}") from None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ResumeError(f"{path} is not valid JSON: {exc}") from None
    return Resume(data=data, source=path, notes=_validate(data))
