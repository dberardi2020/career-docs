"""A design space for resume layouts, and a renderer that samples it.

Hand-writing themes does not scale. Four bespoke themes cost several hundred lines
and buy four points in the space; what is actually wanted is *many* candidates to
flip through, because picking is cheap and generating should be too.

So a layout here is not code — it is a `Spec`, a handful of independent choices.
One renderer reads the spec and emits the HTML. Adding a new value to any axis
multiplies the catalogue instead of adding to it.

    palettes (7) x type (4) x header (5) x skills (3) x promo (4)
      x density (3) x grouping (2) = 10,080 layouts

A caveat worth keeping honest: that number is combinatorial, not curated. There
are 28 hand-authored axis values here and one HTML skeleton — variety comes from
multiplying choices, not from 10,080 designs. Widening the space means adding
values or a second skeleton, not raising the multiplier.

Every axis is constrained to stay single-column and >=10pt, so *everything* the
space can produce is submittable. Character comes from colour, type, and the
treatment of details — never from a layout that breaks parsing.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import html as _html
from dataclasses import dataclass as _dataclass
from typing import Callable as _Callable

from . import model
from .model import date_range


def esc(value) -> str:
    """Escape for HTML text. All content routes through this."""
    return _html.escape(str(value or ""), quote=True)


@_dataclass(frozen=True)
class Theme:
    """A renderable layout, plus the claims the linter checks it against.

    Everything the generator produces is single-column and >=10pt, so these are
    constant today — safe by construction rather than by inspection. They stay
    declared because imported or hand-written layouts will not have that
    guarantee, and the linter should be able to judge those too.
    """

    name: str
    description: str
    render: _Callable[..., str]
    columns: int = 1
    min_font_pt: float = 10.0
    remote_assets: bool = False
    ats_safe: bool = True

# ── Axes ──────────────────────────────────────────────────────────────────────

# (name, accent, ink, tint, on-dark accent)
PALETTES = [
    ("harbor",   "#0b6fa4", "#0f172a", "#eaf4fa", "#8ed6fb"),
    ("ink",      "#2b3445", "#14181f", "#eef0f4", "#b8c2d4"),
    ("moss",     "#2f6b46", "#14251c", "#e8f2ec", "#8fd3ae"),
    ("clay",     "#a4522a", "#2a1a13", "#f7ece5", "#f0b48c"),
    ("plum",     "#6b3f8f", "#221630", "#f1eaf7", "#c9a6e6"),
    ("slate",    "#41556b", "#1a222c", "#eceff3", "#a9bdd2"),
    ("crimson",  "#9b2c39", "#2a1216", "#f9eaec", "#f0a3ad"),
]

# (name, body stack, display stack, is_serif)
TYPEFACES = [
    ("grotesk", '"Segoe UI", -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif',
     '"Segoe UI", -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif', False),
    ("humanist", 'Optima, Candara, "Gill Sans", "Trebuchet MS", sans-serif',
     'Optima, Candara, "Gill Sans", "Trebuchet MS", sans-serif', False),
    ("charter", 'Charter, "Bitstream Charter", Georgia, "Times New Roman", serif',
     'Charter, "Bitstream Charter", Georgia, serif', True),
    ("mixed", '"Segoe UI", -apple-system, Helvetica, Arial, sans-serif',
     'Charter, Georgia, "Times New Roman", serif', True),
]

HEADERS = ["band", "masthead", "rule", "split", "minimal"]
SKILLS = ["pills", "inline", "grid"]
PROMOS = ["ladder", "badge", "stacked", "inline"]
DENSITIES = [("airy", 1.55, 15), ("normal", 1.45, 11), ("compact", 1.34, 8)]

# How a role with a title history is structured on the page. Two genuinely
# different designs, not two ornaments:
#   grouped — the employer is the heading; each title nests beneath it with its
#             own dates and bullets. Progression reads as one continuous tenure.
#   flat    — each title is its own heading, employer repeated. Progression reads
#             as separate roles, which is what most parsers and screeners expect.
# For a role with no promotion the two render identically — as does the `promo`
# axis, which has nothing to show either.
GROUPINGS = ["grouped", "flat"]


@dataclass(frozen=True)
class Spec:
    palette: int
    typeface: int
    header: str
    skills: str
    promo: str
    density: int
    # Added after the first six. Defaulted so existing positional construction
    # keeps working, and named last so it reads at the end of a spec name.
    grouping: str = "grouped"

    @property
    def name(self) -> str:
        """Stable, readable id — every axis spelled out, in axis order.

        Written out rather than encoded, because a spec name is what you save,
        share and publish against. An earlier scheme packed three axes into
        positional digits (`harbor-321-mixed-compact`), which was undecodable
        without the source and, worse, unstable: inserting a value into HEADERS
        renumbered every existing name, so a published spec silently came to
        mean a different layout. Spelling the values out costs characters and
        buys permanence.
        """
        return "-".join((
            PALETTES[self.palette][0],
            TYPEFACES[self.typeface][0],
            self.header,
            self.skills,
            self.promo,
            DENSITIES[self.density][0],
            self.grouping,
        ))

    @property
    def description(self) -> str:
        return (f"{PALETTES[self.palette][0]} · {TYPEFACES[self.typeface][0]} · "
                f"{self.header} header · {self.skills} skills · "
                f"{self.promo} promo · {DENSITIES[self.density][0]} · "
                f"{self.grouping}")


# A handful of named starting points. Each is just a Spec — presets are a
# convenience for people who do not want to browse, not a separate system.
PRESETS = {
    "default":   Spec(0, 0, "band", "pills", "ladder", 1),      # harbor, grotesk
    "plain":     Spec(1, 0, "rule", "inline", "inline", 1),     # ink, understated
    "editorial": Spec(1, 2, "masthead", "inline", "stacked", 1),  # serif, classic
    "warm":      Spec(3, 1, "split", "pills", "badge", 1),      # clay, humanist
}


def preset(name: str) -> Spec | None:
    return PRESETS.get(name)


def all_specs() -> list[Spec]:
    return [Spec(p, t, h, s, pr, d, g)
            for p in range(len(PALETTES))
            for t in range(len(TYPEFACES))
            for h in HEADERS
            for s in SKILLS
            for pr in PROMOS
            for d in range(len(DENSITIES))
            for g in GROUPINGS]


# ── CSS ───────────────────────────────────────────────────────────────────────

def _page_rules(full_bleed: bool, pad: str) -> str:
    """Page boxes, and the reason the bleeding header needs two of them.

    The `band` header is a dark banner that runs to the paper edge, which needs a
    page with no margin. Setting that globally is what produced the bug this
    guards: *every* page lost its margins, so a resume that ran to a second page
    put body text 1.6pt from the edge — off the printable area of most printers,
    and inside the region ATS parsers routinely crop.

    So the bleed is scoped to the first page, where the banner actually is.
    Subsequent pages keep normal vertical margins. Horizontal padding comes from
    `.wrap` in the bleeding case, so body text stays inset on every page.
    """
    if not full_bleed:
        return f"@page {{ size: Letter; margin: 0.55in {pad}; }}"
    return (f"@page {{ size: Letter; margin: 0.55in 0; }}\n"
            f"@page :first {{ margin: 0 0 0.55in; }}")


def css(spec: Spec) -> str:
    _, accent, ink, tint, on_dark = PALETTES[spec.palette]
    _, body_font, display_font, _ = TYPEFACES[spec.typeface]
    _, leading, entry_gap = DENSITIES[spec.density]
    pad = {"airy": "0.72in", "normal": "0.62in", "compact": "0.5in"}[
        DENSITIES[spec.density][0]]
    full_bleed = spec.header == "band"

    return f"""
{_page_rules(full_bleed, pad)}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:{body_font}; font-size:10.5pt; line-height:{leading};
        color:{ink}; background:#fff; }}
h1 {{ font-family:{display_font}; font-size:24pt; font-weight:700;
      letter-spacing:-0.3px; line-height:1.1; }}
.label {{ margin-top:4px; font-size:10.8pt; font-weight:600; }}
.contact {{ margin-top:8px; font-size:10pt; }}
.contact a {{ text-decoration:none; color:inherit; }}
.contact .bit {{ white-space:nowrap; }}
.contact .sep {{ opacity:.5; padding:0 4px; }}
.wrap {{ {"padding:0.3in " + pad + " 0.4in;" if full_bleed else ""} }}
/* `@page` margins apply to print only, so on screen a layout would have no
   inset whatsoever — text running to the very edge of every preview, which is
   exactly what the viewer shows. The bleeding header supplies its own inset via
   `.wrap`; everything else needs the page margin mirrored here. */
@media screen {{
  body {{ padding: {"0" if full_bleed else f"0.55in {pad}"}; }}
}}
h2 {{ font-family:{display_font}; font-size:10.4pt; font-weight:700;
      text-transform:uppercase; letter-spacing:1.1px; color:{accent};
      margin:{entry_gap + 4}px 0 6px; padding-bottom:3px;
      border-bottom:1.5px solid {tint}; }}
.summary {{ margin-top:11px; }}
.entry {{ margin-bottom:{entry_gap}px; break-inside:avoid-page; }}
.entry-head {{ font-size:10.9pt; font-weight:700; }}
.entry-meta {{ font-size:10pt; opacity:.72; margin-top:1px; }}
ul {{ margin:5px 0 0 17px; }}
li {{ margin-bottom:3px; }}
li::marker {{ color:{accent}; }}
a {{ color:{accent}; text-decoration:none; }}

/* header: band */
.hdr-band {{ background:{ink}; color:#fff; padding:0.42in {pad} 0.34in; }}
.hdr-band h1 {{ color:#fff; }}
.hdr-band .label {{ color:{on_dark}; }}
.hdr-band .contact {{ color:#dfe5ee; }}
/* header: masthead */
.hdr-masthead {{ text-align:center; padding-bottom:10px;
                 border-bottom:2px solid {ink}; }}
.hdr-masthead h1 {{ letter-spacing:1.2px; text-transform:uppercase; font-size:22pt; }}
.hdr-masthead .label {{ font-style:italic; opacity:.8; }}
/* header: rule */
.hdr-rule {{ padding-bottom:9px; border-bottom:3px solid {accent}; }}
.hdr-rule .label {{ color:{accent}; }}
/* header: split */
.hdr-split {{ display:flex; align-items:flex-end; gap:18px;
              padding-bottom:9px; border-bottom:1px solid {tint}; }}
/* The contact column is full of nowrap items, so without a min-width the name
   column collapses and a two-word name wraps mid-name. */
.hdr-split .who {{ flex:1 1 auto; min-width:3.1in; }}
.hdr-split .contact {{ flex:0 1 auto; text-align:right; font-size:9.4pt;
                       margin-top:0; line-height:1.5; }}
.hdr-split .label {{ color:{accent}; }}
/* header: minimal */
.hdr-minimal h1 {{ font-size:19pt; }}
.hdr-minimal .label {{ opacity:.75; font-weight:500; }}

/* skills */
/* Grouping is carried entirely by spacing, so the gap *between* groups has to
   decisively beat the gap *within* one: `.pills` gap applies on both axes, so a
   wrapped second line of pills sits at that gap — keep it tighter than the grid
   row-gap, or every group melts into one field of pills.
   The label column is `min-content`: exactly the widest unbreakable label word,
   so that word sits flush on the content edge and every other label right-aligns
   to it. Any fixed basis leaves a ragged gutter instead — right-aligned text only
   reaches the left edge when a line happens to fill the column exactly, which is
   coincidence, not alignment. Labels still wrap freely inside the column. */
.skill-rows {{ display:grid; grid-template-columns:min-content 1fr;
               column-gap:9px; row-gap:10px; align-items:baseline; }}
.skill-row {{ display:contents; }}
.skill-label {{ text-align:right; font-size:9.6pt;
                font-weight:700; opacity:.85; line-height:1.3; }}
.pills {{ display:flex; flex-wrap:wrap; gap:3px 4px; }}
.pill {{ background:{tint}; color:{accent}; border:0.5pt solid {accent}33;
         border-radius:3pt; padding:1pt 5.5pt; font-size:9.5pt; font-weight:600; }}
.skill-inline {{ margin-bottom:3px; }}
.skill-inline b {{ color:{accent}; }}
.skill-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:2px 18px; }}

/* promotion treatments */
.promo-badge {{ display:inline-block; width:auto; max-width:max-content;
                background:{accent}; color:#fff; border-radius:20px;
                padding:0.5pt 7pt; font-size:8.6pt; font-weight:700;
                letter-spacing:.4px; margin-left:7px; vertical-align:2px;
                text-align:center; white-space:nowrap; }}
.promo-ladder {{ font-size:9.8pt; opacity:.78; margin-top:2px; }}
.promo-ladder .arrow {{ color:{accent}; font-weight:700; padding:0 4px; }}

/* Title history within one employer. Each stint owns its bullets, so the title
   line has to read as a heading for what follows, not as a caption on what came
   before — hence the weight, and the rule that ties the run together. */
.stints {{ margin-top:5px; }}
.stint {{ margin-top:6px; }}
.stint:first-child {{ margin-top:3px; }}
.stint-title {{ font-size:10.4pt; font-weight:700; color:{accent}; }}
.stint-title .when {{ float:right; font-weight:400; font-size:9.6pt;
                      color:inherit; opacity:.7; }}
.stint-when {{ font-size:9.6pt; opacity:.66; margin-top:1px; }}
.stint ul {{ margin-top:4px; }}
/* ladder: a spine down the run of titles, so promotion reads as one tenure */
.promo-ladder.stints, .stints.promo-ladder {{ }}
.stints.promo-ladder .stint {{ padding-left:11px; border-left:2px solid {tint}; }}
.stints.promo-ladder .stint.current {{ border-left-color:{accent}; }}
/* stacked: title and dates on separate lines, with air between stints */
.stints.promo-stacked .stint {{ margin-top:9px; }}
/* inline: quietest — title and dates run together, no rules */
.stints.promo-inline .stint-title {{ font-weight:600; }}
.promo-stacked {{ margin-top:3px; padding-left:9px;
                  border-left:2.5px solid {accent}; font-size:9.8pt; }}
.promo-stacked .then {{ opacity:.65; }}
.promo-inline {{ font-size:10pt; font-style:italic; opacity:.72; }}
/* A promotion is worth marking, not muting — so the note carries the accent at
   full strength. Scoped to `.note` rather than folded into `.promo-inline`,
   because that class also lands on the *stints container* when promo=inline
   (see `_stint_block`), where accenting a whole block of titles would be wrong. */
.note {{ color:{accent}; font-weight:600; opacity:1; }}
"""


# ── Fragments ─────────────────────────────────────────────────────────────────

def _contact_bits(resume) -> list[str]:
    bits = [esc(resume.basics.get("phone")), esc(resume.location)]
    if email := resume.basics.get("email"):
        bits.append(f'<a href="mailto:{esc(email)}">{esc(email)}</a>')
    for profile in resume.profiles:
        if url := profile.get("url"):
            shown = url.replace("https://", "").replace("http://", "").replace("www.", "")
            bits.append(f'<a href="{esc(url)}">{esc(shown)}</a>')
    return [b for b in bits if b]


def _contact(resume) -> str:
    sep = ' <span class="sep">·</span> '
    return ('<div class="contact">'
            + sep.join(f'<span class="bit">{b}</span>' for b in _contact_bits(resume))
            + "</div>")


def _header(resume, spec: Spec) -> str:
    name = f"<h1>{esc(resume.name)}</h1>"
    label = f'<div class="label">{esc(resume.label)}</div>' if resume.label else ""
    if spec.header == "split":
        return (f'<header class="hdr-split"><div class="who">{name}{label}</div>'
                f"{_contact(resume)}</header>")
    return (f'<header class="hdr-{spec.header}">{name}{label}'
            f"{_contact(resume)}</header>")



def _entry_head(entry, spec: Spec) -> str:
    """The role heading.

    With a title history the employer *is* the heading, and each title appears
    once below it with its own dates and bullets. Repeating the current title
    here would print it twice.
    """
    if model.stints(entry):
        head = esc(entry.get("name", ""))
        if spec.promo == "badge":
            head += '<span class="promo-badge">&uarr; PROMOTED</span>'
        return head
    return " - ".join(x for x in (esc(entry.get("position", "")),
                                  esc(entry.get("name", ""))) if x)


def _bullet_list(highlights) -> str:
    if not highlights:
        return ""
    return "<ul>" + "".join(f"<li>{esc(h)}</li>" for h in highlights) + "</ul>"


def _bullets(entry) -> str:
    return _bullet_list(entry.get("highlights") or [])


def _stint_block(entry, spec: Spec) -> str:
    """Each title held at one employer, with the bullets earned under it.

    The promo axis chooses how the title line reads; it no longer chooses
    whether the progression is visible at all. Every treatment shows each
    stint's own bullets, because that is the thing a promotion is evidence of.
    """
    history = model.stints(entry)
    if not history:
        return ""

    rows = []
    for index, stint in enumerate(history):
        title = esc(stint.get("position", ""))
        when = date_range(stint.get("startDate"), stint.get("endDate"))
        current = index == 0

        if spec.promo == "ladder":
            line = (f'<div class="stint-title">{title}'
                    f'<span class="when">{esc(when)}</span></div>')
        elif spec.promo == "stacked":
            line = (f'<div class="stint-title">{title}</div>'
                    f'<div class="stint-when">{esc(when)}</div>')
        elif spec.promo == "badge":
            mark = '<span class="promo-badge">&uarr; PROMOTED</span>' if current else ""
            line = (f'<div class="stint-title">{title}{mark}'
                    f'<span class="when">{esc(when)}</span></div>')
        else:  # inline
            line = (f'<div class="stint-title">{title} '
                    f'<span class="when">&middot; {esc(when)}</span></div>')

        rows.append(f'<div class="stint{" current" if current else ""}">'
                    f'{line}{_bullet_list(stint.get("highlights") or [])}</div>')
    return f'<div class="stints promo-{esc(spec.promo)}">' + "".join(rows) + "</div>"


def _skills(resume, spec: Spec) -> str:
    groups = [g for g in resume.skills if g.get("keywords")]
    if not groups:
        return ""
    if spec.skills == "pills":
        # One grid over every row, so the label column resolves against all the
        # labels at once — per-row boxes could only size against their own.
        rows = '<div class="skill-rows">' + "".join(
            f'<div class="skill-row"><div class="skill-label">{esc(g.get("name",""))}</div>'
            f'<div class="pills">'
            + "".join(f'<span class="pill">{esc(k)}</span>' for k in g["keywords"])
            + "</div></div>" for g in groups) + "</div>"
    elif spec.skills == "grid":
        rows = ('<div class="skill-grid">' + "".join(
            f'<div class="skill-inline"><b>{esc(g.get("name",""))}:</b> '
            f'{esc(", ".join(g["keywords"]))}</div>' for g in groups) + "</div>")
    else:
        rows = "".join(
            f'<div class="skill-inline"><b>{esc(g.get("name",""))}:</b> '
            f'{esc(", ".join(g["keywords"]))}</div>' for g in groups)
    return "<h2>Skills</h2>" + rows


def _note(entry) -> str:
    return (f'<div class="promo-inline note">{esc(entry["note"])}</div>'
            if entry.get("note") else "")


def _work_grouped(entry, spec: Spec) -> str:
    """Employer as the heading, each title nested beneath it."""
    meta = " | ".join(x for x in (
        esc(entry.get("location")),
        date_range(entry.get("startDate"), entry.get("endDate"))) if x)
    return (f'<div class="entry"><div class="entry-head">'
            f'{_entry_head(entry, spec)}</div>'
            f'<div class="entry-meta">{meta}</div>'
            f"{_note(entry)}{_bullets(entry)}{_stint_block(entry, spec)}</div>")


def _work_flat(entry, spec: Spec) -> str:
    """Each title its own heading, employer repeated — one block per stint.

    Company-level bullets ride with the most recent title, since that is where a
    reader looks first and they describe the tenure as a whole.
    """
    history = model.stints(entry)
    if not history:
        return _work_grouped(entry, spec)

    employer = esc(entry.get("name", ""))
    blocks = []
    for index, stint in enumerate(history):
        head = " - ".join(x for x in (esc(stint.get("position", "")), employer) if x)
        if spec.promo == "badge" and index == 0:
            head += '<span class="promo-badge">&uarr; PROMOTED</span>'
        meta = " | ".join(x for x in (
            esc(entry.get("location")),
            date_range(stint.get("startDate"), stint.get("endDate"))) if x)
        bullets = list(stint.get("highlights") or [])
        if index == 0:
            bullets = list(entry.get("highlights") or []) + bullets
        blocks.append(f'<div class="entry"><div class="entry-head">{head}</div>'
                      f'<div class="entry-meta">{meta}</div>'
                      f'{_note(entry) if index == 0 else ""}'
                      f"{_bullet_list(bullets)}</div>")
    return "".join(blocks)


def _work(resume, spec: Spec) -> str:
    if not resume.work:
        return ""
    render_entry = _work_flat if spec.grouping == "flat" else _work_grouped
    return "<h2>Experience</h2>" + "".join(
        render_entry(entry, spec) for entry in resume.work)


def _education(resume) -> str:
    if not resume.education:
        return ""
    rows = []
    for entry in resume.education:
        study = " ".join(esc(v) for v in (entry.get("studyType"),
                                          entry.get("area")) if v)
        meta = [study, esc(entry.get("location"))]
        if end := entry.get("endDate"):
            meta.append(f"Graduated {date_range(end, end).split(' - ')[0]}")
        if score := entry.get("score"):
            meta.append(f"GPA {esc(score)}")
        rows.append(f'<div class="entry"><div class="entry-head">'
                    f'{esc(entry.get("institution",""))}</div>'
                    f'<div class="entry-meta">{", ".join(m for m in meta if m)}</div></div>')
    return "<h2>Education</h2>" + "".join(rows)


def render(resume, spec: Spec) -> str:
    summary = (f'<div class="summary">{esc(resume.summary)}</div>'
               if resume.summary else "")
    body = (summary + _skills(resume, spec) + _work(resume, spec)
            + _education(resume))
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        f"<title>{esc(resume.name)} - Resume</title><style>{css(spec)}</style>"
        f"</head><body>{_header(resume, spec)}"
        f'<div class="wrap">{body}</div></body></html>\n'
    )


def as_theme(spec: Spec) -> Theme:
    """Wrap a spec so it moves through the same pipeline as a hand-built theme."""
    return Theme(
        name=spec.name,
        description=spec.description,
        render=lambda resume, _s=spec: render(resume, _s),
        columns=1,
        min_font_pt=10.0,
        remote_assets=False,
        ats_safe=True,
    )
