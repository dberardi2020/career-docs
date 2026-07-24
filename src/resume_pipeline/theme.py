"""The site's design kit — one source of truth for every hosted surface.

**Midnight Indigo**: a committed dark identity — a dark blue-slate ground with a
periwinkle accent and a warm-gold secondary, chosen so the white résumé previews
pop against the chrome. The ground and text are kept *neutral* (a slate biased
only faintly toward blue) so the periwinkle reads as a deliberate accent rather
than the whole page being purple.

Two exports, both injected by the landing (`demo.py`) and the layout browser
(`viewer.py`) so the two surfaces share the *same components*, not just the same
colours:

- ``TOKENS`` — the design variables (`:root`). A superset of every custom-property
  name either surface used, with aliases (`--panel`≡`--card`, `--btn`≡`--panel2`,
  `--mute`≡`--muted`, `--btn-line`≡`--line2`), so neither file's component CSS had
  to be renamed.
- ``BASE`` — the shared component layer: reset, links, focus ring, the brand
  wordmark, one button system, the card surface, the page measure (``.wrap``), the
  eyebrow pill, and the site's nav and footer bands. Both pages render these
  identically; page-specific CSS only adds what is genuinely unique to it.

``.wrap`` is the load-bearing one: every surface centres its content on the same
column, so the brand, the headings, the controls and the grid all share one left
edge. Full-bleed bands (the nav, the browser's control bar) are the band itself
with a ``.wrap`` inside — which is why ``nav()`` emits a wrapper div.

Deliberately single-theme — it commits to one visual world rather than a
light/dark pair (revisiting that is its own ticket).
"""
from __future__ import annotations

TOKENS = """\
  :root{
    /* ── Midnight Indigo ──────────────────────────────────────────────────
       Neutral dark-slate chrome (a faint blue lean, not purple), one periwinkle
       accent, a warm-gold secondary for relief. The résumé previews are always
       white paper — these style the site around them. */
    --bg:#101423;          /* page ground — dark blue-slate, near-neutral */
    --card:#181d2e;        /* header, cards, panels */
    --panel:#181d2e;       /*   alias of --card (landing) */
    --panel2:#222a3c;      /* elevated surface: buttons */
    --btn:#222a3c;         /*   alias of --panel2 (viewer) */
    --line:#283042;        /* hairlines and borders */
    --line2:#39435a;       /* stronger borders */
    --btn-line:#39435a;    /*   alias of --line2 (viewer) */
    --ink:#e7e9f0;         /* primary text — neutral cool white */
    --muted:#8e96a8;       /* secondary text — a blue-grey, picked not defaulted */
    --mute:#8e96a8;        /*   alias of --muted (landing) */
    --accent:#8f7bff;      /* periwinkle — the one bold note */
    --accent-2:#a493ff;    /* a touch brighter, for hover */
    --accent-ink:#101127;  /* text that sits on the accent */
    --accent-soft:color-mix(in srgb,var(--accent) 13%,transparent);
    --gold:#eab35c;        /* warm secondary — used sparingly, for relief */
    --shadow:0 1px 2px rgba(0,0,0,.5),0 14px 34px rgba(0,0,0,.46);
    --maxw:1120px;         /* the page measure — every surface centres on this column */
    --radius:13px;         /* cards, panels */
    --radius-sm:9px;       /* buttons, controls */
    --radius-pill:999px;   /* pills, chips, swatches */
    --font-body:system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
    --font-mono:ui-monospace,"SF Mono",Menlo,"Cascadia Code","Roboto Mono",monospace;
  }
"""

BASE = """\
  *{box-sizing:border-box}
  /* Every component below sets `display`, which silently beats the UA's
     `[hidden]{display:none}` — so a `hidden` button or bar stayed on screen (the
     static catalogue was offering an Export PDF it has no backend for). Any rule
     that wants to hide by attribute needs this to outrank the component. */
  [hidden]{display:none!important}
  a{color:var(--accent);text-decoration:none}
  a:hover{text-decoration:underline}
  :focus-visible{outline:2px solid var(--accent);outline-offset:2px}

  /* Brand wordmark — identical on both surfaces. */
  .brand{font-weight:800;font-size:15.5px;letter-spacing:-.01em;color:var(--ink);text-decoration:none}
  .brand span{color:var(--accent)}
  .brand:hover{text-decoration:none}

  /* One button system. `button` (element) and `.btn` (for anchors) share it, so a
     link-styled CTA on the landing and a real button in the viewer match. Size
     modifier `.lg` for hero CTAs; `.primary` fills with the accent; `.ghost` is
     a quiet text button. Component classes (.fpill, .chip …) override as needed. */
  button,.btn{font:inherit;font-weight:600;font-size:13px;line-height:1.1;color:var(--ink);
       background:var(--panel2);border:1px solid var(--line2);border-radius:var(--radius-sm);
       padding:8px 14px;cursor:pointer;white-space:nowrap;display:inline-flex;align-items:center;
       justify-content:center;gap:7px;text-decoration:none;
       transition:border-color .12s,background .12s,color .12s,filter .12s}
  button:hover,.btn:hover{border-color:var(--accent);color:var(--accent);text-decoration:none}
  .btn.lg{font-size:14.5px;padding:12px 20px;border-radius:var(--radius)}
  button.primary,.btn.primary{background:var(--accent);border-color:var(--accent);
       color:var(--accent-ink);font-weight:700}
  button.primary:hover,.btn.primary:hover{filter:brightness(1.07);background:var(--accent);
       border-color:var(--accent);color:var(--accent-ink)}
  .btn.ghost{background:transparent;border-color:transparent;color:var(--muted)}
  .btn.ghost:hover{color:var(--ink);border-color:var(--line2)}

  /* Card / panel surface. */
  .card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);
        box-shadow:var(--shadow)}

  /* The page measure. Every surface centres its content on this one column, so the
     brand, the headings, the controls and the grid all share a left edge — full-bleed
     bands (the nav, the browser's control bar) are the band itself, with a `.wrap`
     inside carrying the content. Pages add their own vertical padding. */
  .wrap{max-width:var(--maxw);margin:0 auto;padding:0 22px}

  /* The eyebrow above a headline: a small capitalised label with a lit dot. */
  .pill{display:inline-flex;align-items:center;gap:8px;font-size:11px;letter-spacing:.09em;
        text-transform:uppercase;color:var(--muted);border:1px solid var(--line);
        border-radius:var(--radius-pill);padding:5px 12px}
  .pill b{width:6px;height:6px;border-radius:50%;background:var(--gold);
          box-shadow:0 0 9px var(--gold)}

  /* The site's top bar — the SAME on the landing and the browser, so the browser
     reads as a page of the site (and always links back to the front door via the
     brand). A full-bleed blurred band; the content inside rides the page measure so
     the brand lines up with the headline beneath it. */
  .sitenav{position:sticky;top:0;z-index:40;border-bottom:1px solid var(--line);
           background:color-mix(in srgb,var(--bg) 86%,transparent);backdrop-filter:blur(10px)}
  .sitenav-in{display:flex;align-items:center;gap:16px;padding-top:12px;padding-bottom:12px}
  .sitenav-links{display:flex;align-items:center;gap:9px;margin-left:auto}
  .sitenav .btn{font-size:13px;padding:8px 13px}

  /* The site's footer — one rule, both surfaces. */
  .sitefoot{border-top:1px solid var(--line);padding-top:20px;display:flex;flex-wrap:wrap;
            gap:8px 16px;align-items:center;color:var(--muted);font-size:12.5px}
  .sitefoot .sep{opacity:.4}
"""


# The repository, shown in navs and footers.
REPO = "https://github.com/dberardi2020/resume-pipeline"


def nav(cta: str = "") -> str:
    """The shared top bar. The brand always links to the front door (``./``); `cta`
    is the right-aligned links, which differ per page."""
    return ('<nav class="sitenav"><div class="wrap sitenav-in">'
            '<a class="brand" href="./">Resume<span>Pipeline</span></a>'
            f'<span class="sitenav-links">{cta}</span></div></nav>')


def footer(note: str = "") -> str:
    """The shared footer. `note` is the page-specific trailing sentence."""
    tail = f'<span class="sep">·</span><span>{note}</span>' if note else ""
    return ('<footer class="sitefoot"><span>Resume Pipeline</span><span class="sep">·</span>'
            '<span>MIT licensed</span><span class="sep">·</span>'
            f'<a href="{REPO}">Source on GitHub</a>{tail}</footer>')
