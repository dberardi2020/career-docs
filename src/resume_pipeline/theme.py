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
  wordmark, one button system, and the card surface. Both pages render these
  identically; page-specific CSS only adds what is genuinely unique to it.

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
    --radius:13px;         /* cards, panels */
    --radius-sm:9px;       /* buttons, controls */
    --radius-pill:999px;   /* pills, chips, swatches */
    --font-body:system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
    --font-mono:ui-monospace,"SF Mono",Menlo,"Cascadia Code","Roboto Mono",monospace;
  }
"""

BASE = """\
  *{box-sizing:border-box}
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

  /* The site's top bar — the SAME on the landing and the browser, so the browser
     reads as a page of the site (and always links back to the front door via the
     brand). Sticky, with a blurred ground. */
  .sitenav{position:sticky;top:0;z-index:40;display:flex;align-items:center;gap:16px;
           padding:12px 22px;border-bottom:1px solid var(--line);
           background:color-mix(in srgb,var(--bg) 86%,transparent);backdrop-filter:blur(10px)}
  .sitenav-links{display:flex;align-items:center;gap:9px;margin-left:auto}
  .sitenav .btn{font-size:13px;padding:8px 13px}
"""


# The repository, shown in navs and footers.
REPO = "https://github.com/dberardi2020/resume-pipeline"


def nav(cta: str = "") -> str:
    """The shared top bar. The brand always links to the front door (``./``); `cta`
    is the right-aligned links, which differ per page."""
    return ('<nav class="sitenav"><a class="brand" href="./">Resume<span>Pipeline</span></a>'
            f'<span class="sitenav-links">{cta}</span></nav>')
