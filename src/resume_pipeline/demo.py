"""Bake the whole design space into a static, no-backend demo (RP-0038).

`serve` needs a process: the grid asks `/api/page` for a filtered page and pulls
each preview from `/preview/<spec>`. A hosted demo has no process — just files on
GitHub Pages — so both of those have to move into the browser.

Paging and filtering are pure functions of the spec name, so they port to JS
trivially. Rendering is the hard part: it is the Python renderer. But a rendered
layout separates cleanly (proven across all 10,080 specs):

- its `<body>` markup depends only on (header, skills, promo, grouping) — **120**;
- its `<style>` depends only on (palette, typeface, density, header==band) — **168**.

So the browser can rebuild *any* of the 10,080 previews from those two small tables
— which are the *real* renderer's output, baked once at build time. No second
renderer, no drift: `bake()` is the only place layout HTML comes from, same as
`serve`. The tables are ~1MB, dominated by 120 near-identical resume bodies, and
gzip to a fraction of that.
"""
from __future__ import annotations

import html as _html
import re
from pathlib import Path

from . import compose, space, theme, viewer

# render() emits a fixed skeleton; these lift the two spec-dependent spans out of it.
_STYLE = re.compile(r"<style>(.*?)</style>", re.S)
_BODY = re.compile(r"</head><body>(.*?)</body></html>", re.S)


def markup_key(spec: compose.Spec) -> str:
    """The axes that decide the body markup. Must match the JS side exactly."""
    return "|".join((spec.header, spec.skills, spec.promo, spec.grouping))


def css_key(spec: compose.Spec) -> str:
    """The axes that decide the stylesheet — palette/typeface/density, and whether
    the header bleeds (only `band` does), which changes the page boxes."""
    return "|".join((str(spec.palette), str(spec.typeface), str(spec.density),
                     "1" if spec.header == "band" else "0"))


def bake(resume) -> dict:
    """The two lookup tables plus the constant title, enough to rebuild every
    preview in the browser.

    Renders 120 bodies (one per markup key) and calls `compose.css` 168 times (one
    per style key) — not the whole space — because the invariant lets each table be
    filled from a single representative per key.
    """
    markups: dict[str, str] = {}
    for header in compose.HEADERS:
        for skills in compose.SKILLS:
            for promo in compose.PROMOS:
                for grouping in compose.GROUPINGS:
                    spec = compose.Spec(0, 0, header, skills, promo, 1, grouping)
                    key = markup_key(spec)
                    if key not in markups:
                        markups[key] = _BODY.search(compose.render(resume, spec)).group(1)

    css: dict[str, str] = {}
    for palette in range(len(compose.PALETTES)):
        for typeface in range(len(compose.TYPEFACES)):
            for density in range(len(compose.DENSITIES)):
                for header in ("band", "rule"):   # bleeding vs not — the only css split header makes
                    spec = compose.Spec(palette, typeface, header, "pills", "ladder", density, "grouped")
                    css[css_key(spec)] = compose.css(spec)

    return {"title": compose.esc(resume.name), "markups": markups, "css": css}


# ── The hosted site ────────────────────────────────────────────────────────────

REPO = theme.REPO

# The hero carousel's five layouts. Curated, not `spread`d: the eye reads *palette*
# first, so the five are chosen to vary colour, header treatment AND typeface on
# purpose — variety is what makes the carousel worth watching (spread maximises
# Hamming distance across all seven axes, which can leave the palette barely moving).
# One per header treatment, five distinct palettes.
# palette idx: harbor 0 · ink 1 · moss 2 · clay 3 · plum 4 · slate 5 · crimson 6
# typeface idx: grotesk 0 · humanist 1 · charter 2 · mixed 3   density idx: airy 0 · normal 1 · compact 2
HERO_SPECS = [
    compose.Spec(2, 0, "band",     "pills",  "ladder",  1, "grouped"),  # moss · grotesk · dark band
    compose.Spec(6, 2, "masthead", "inline", "stacked", 1, "flat"),     # crimson · charter · centred serif
    compose.Spec(0, 1, "split",    "grid",   "badge",   1, "grouped"),  # harbor · humanist · split
    compose.Spec(3, 3, "rule",     "pills",  "inline",  1, "flat"),     # clay · mixed · accent rule
    compose.Spec(4, 2, "minimal",  "inline", "stacked", 1, "grouped"),  # plum · charter · minimal
]

# A product landing, not a raw tool. Self-contained and dependency-free (no CDN
# fonts) to match the renderer's ethos and stay instant on a shared link. Copy
# describes only what is real today — there is deliberately no teaser for anything
# unbuilt. Dark, and cohesive with the viewer it links to.
_LANDING = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Resume Pipeline — a design space of __TOTAL__ resume layouts</title>
<meta name="description" content="One structured profile becomes __TOTAL__ parse-safe resume layouts. Browse the whole space in your browser — no install, no account, nothing real behind it.">
<style>
  /* Design kit (tokens + shared components: reset, links, brand, buttons, card,
     site nav) — one source of truth in theme.py, shared with the browser page. */
__KIT__
  html,body{margin:0}
  body{background:var(--bg);color:var(--ink);font-family:var(--font-body);font-size:15px;
       line-height:1.6;-webkit-font-smoothing:antialiased}

  .wrap{max-width:1120px;margin:0 auto;padding:34px 22px 90px}

  .hero{display:grid;grid-template-columns:1.05fr .95fr;gap:44px;align-items:center;margin:20px 0 6px}
  .pill{display:inline-flex;align-items:center;gap:8px;font-size:11px;letter-spacing:.09em;
        text-transform:uppercase;color:var(--mute);border:1px solid var(--line);
        border-radius:var(--radius-pill);padding:5px 12px}
  .pill b{width:6px;height:6px;border-radius:50%;background:var(--gold);
          box-shadow:0 0 9px var(--gold)}
  h1{font-size:44px;line-height:1.06;font-weight:800;letter-spacing:-.02em;margin:18px 0 14px}
  .sub{color:var(--mute);font-size:16px;max-width:54ch;margin:0 0 24px}
  .sub b{color:var(--ink);font-weight:500}
  .cta{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:16px}
  .fine{font-size:12.5px;color:var(--mute);margin:2px 0 0}

  /* Hero stage: a carousel of live renders of the same profile, one large at a time,
     crossfading. Real output, not screenshots — the same thing the browser shows. */
  .stagewrap{display:flex;flex-direction:column;gap:13px}
  .stage{position:relative;aspect-ratio:816/620;background:#fff;border:1px solid var(--line);
         border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow)}
  /* A sliding track — one résumé at a time, sliding to the next. No crossfade, so
     two text-dense pages never ghost through each other. */
  .track{display:flex;height:100%;transition:transform .8s cubic-bezier(.4,0,.2,1);will-change:transform}
  .slide{position:relative;flex:0 0 100%;height:100%;overflow:hidden}
  .slide iframe{position:absolute;top:0;left:0;width:816px;height:1056px;border:0;
                transform-origin:top left;pointer-events:none}
  @media (prefers-reduced-motion:reduce){ .track{transition:none} }
  .dots{display:flex;justify-content:center;gap:7px}
  .dot{width:7px;height:7px;padding:0;border:0;border-radius:50%;cursor:pointer;
       background:var(--line2);transition:.2s}
  .dot:hover{background:var(--mute)}
  .dot.on{background:var(--accent);width:22px;border-radius:4px}
  /* Manual advance: prev/next, revealed on hover (hovering also pauses auto-advance). */
  .arrow{position:absolute;top:50%;transform:translateY(-50%);z-index:3;width:36px;height:36px;padding:0;
         border-radius:50%;border:1px solid var(--line2);color:var(--ink);cursor:pointer;
         background:color-mix(in srgb,var(--bg) 80%,transparent);backdrop-filter:blur(4px);
         font-size:19px;line-height:1;display:flex;align-items:center;justify-content:center;
         opacity:0;transition:opacity .15s,background .15s;box-shadow:var(--shadow)}
  .stage:hover .arrow,.arrow:focus-visible{opacity:1}
  .arrow:hover{background:var(--bg);border-color:var(--mute)}
  .arrow.prev{left:11px} .arrow.next{right:11px}

  .strip{margin-top:58px;border-top:1px solid var(--line);padding-top:30px}
  .strip h2{font-size:13px;letter-spacing:.02em;color:var(--mute);font-weight:600;margin:0 0 18px;text-transform:none}
  .cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
  .c{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:20px 19px}
  .c h3{font-size:16.5px;font-weight:700;margin:0 0 7px;letter-spacing:-.01em}
  .c p{color:var(--mute);font-size:13.5px;margin:0}
  .c p b{color:var(--ink);font-weight:500}

  footer{margin-top:56px;padding-top:20px;border-top:1px solid var(--line);
         display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;color:var(--mute);font-size:12.5px}
  footer .sep{opacity:.4}

  @media (max-width:860px){
    .hero{grid-template-columns:1fr;gap:30px}
    h1{font-size:34px}
    .cards{grid-template-columns:1fr}
  }
</style></head><body>
__NAV__
<main class="wrap">
  <section class="hero">
    <div>
      <span class="pill"><b></b>Live demo · sample profile</span>
      <h1>Your resume is data, not a document.</h1>
      <p class="sub">One structured profile becomes a space of <b>__TOTAL__ parse-safe layouts</b>.
        Browse the whole space right here — hold a colour or typeface, page through, open any
        layout. <b>No install, no account</b>, nothing real behind it.</p>
      <div class="cta">
        <a class="btn primary lg" href="./browse.html">Browse the layouts →</a>
        <a class="btn lg" href="__REPO__">View the source</a>
      </div>
      <p class="fine">A live demo over a sample profile (Jane Smith). The full tool — editing,
        linting and publishing — runs in your coding agent.</p>
    </div>
    <div class="stagewrap">
      <div class="stage" id="stage"><div class="track" id="track">__STAGE__</div><button class="arrow prev" id="prev" aria-label="Previous layout">‹</button><button class="arrow next" id="next" aria-label="Next layout">›</button></div>
      <div class="dots" id="dots"></div>
    </div>
  </section>

  <section class="strip">
    <h2>Generated, not templated.</h2>
    <div class="cards">
      <div class="c">
        <h3>__TOTAL__ layouts, one profile</h3>
        <p>Seven independent choices — <b>palette, type, header, skills, promotions, density,
          grouping</b> — multiply into a space you browse, instead of a handful of themes
          someone else designed.</p>
      </div>
      <div class="c">
        <h3>Parse-safe by construction</h3>
        <p>Every layout is <b>single-column and ≥10pt</b>, so whatever you pick survives an ATS.
          Character comes from colour, type and the treatment of details — never from a layout
          that breaks parsing.</p>
      </div>
      <div class="c">
        <h3>You own the data</h3>
        <p>One profile is the only thing you edit; the <b>PDF, HTML and Markdown</b> are generated
          from it. What you see in a preview is exactly what publishes.</p>
      </div>
    </div>
  </section>

  <footer>
    <span>Resume Pipeline</span><span class="sep">·</span>
    <span>MIT licensed</span><span class="sep">·</span>
    <a href="__REPO__">Source on GitHub</a><span class="sep">·</span>
    <span>Early — this page is a demo of the layout browser; the full tool runs in your coding agent.</span>
  </footer>
</main>
<script>
  // Hero carousel: one large live render at a time, crossfading through the set.
  // Each slide is a real 816px-wide render scaled to the stage; the dots and auto-
  // advance are the only chrome. Auto-advance pauses on hover and yields entirely to
  // prefers-reduced-motion.
  (function(){
    const stage=document.getElementById("stage"), track=document.getElementById("track");
    if(!stage || !track) return;
    const slides=[...track.children];
    const dotsBox=document.getElementById("dots");
    const reduce=matchMedia("(prefers-reduced-motion: reduce)").matches;
    let i=0, timer=null;

    slides.forEach((_,n)=>{
      const d=document.createElement("button");
      d.className="dot"+(n?"":" on");
      d.setAttribute("aria-label","Layout "+(n+1));
      d.onclick=()=>{ go(n); restart(); };
      dotsBox.appendChild(d);
    });
    const dots=[...dotsBox.children];

    function go(n){
      dots[i].classList.remove("on");
      i=(n+slides.length)%slides.length;
      track.style.transform="translateX("+(-i*100)+"%)";
      dots[i].classList.add("on");
    }
    document.getElementById("prev").onclick=()=>{ go(i-1); restart(); };
    document.getElementById("next").onclick=()=>{ go(i+1); restart(); };
    function restart(){ if(timer) clearInterval(timer); if(!reduce) timer=setInterval(()=>go(i+1), 5000); }
    function fit(){
      const s=stage.clientWidth/816;
      slides.forEach(sl=>{ const f=sl.querySelector("iframe"); if(f) f.style.transform="scale("+s+")"; });
    }
    addEventListener("resize", fit);
    slides.forEach(sl=>sl.querySelector("iframe").addEventListener("load", fit));
    stage.addEventListener("mouseenter", ()=>{ if(timer){ clearInterval(timer); timer=null; } });
    stage.addEventListener("mouseleave", restart);
    fit(); restart();
  })();
</script>
</body></html>
"""


def _stage(names) -> str:
    """The hero carousel's slides, each a scaled iframe pointing at a sibling render.
    They sit in a flex track the script slides between."""
    return "".join(
        f'<div class="slide">'
        f'<iframe loading="lazy" scrolling="no" title="{_html.escape(name)}" src="{name}.html"></iframe>'
        f'</div>'
        for name in names
    )


# The right-hand nav links differ per page. On the landing, a Browse CTA; on the
# browser, just GitHub — the brand already links back to the front door.
_NAV_LANDING = (f'<a class="btn ghost" href="{REPO}">GitHub</a>'
                '<a class="btn primary" href="./browse.html">Browse the layouts →</a>')
_NAV_BROWSE = (f'<a class="btn ghost" href="{REPO}">GitHub</a>'
               '<a class="btn ghost" href="./">Overview</a>')


def landing(total: int, stage_names) -> str:
    return (_LANDING.replace("__KIT__", theme.TOKENS + theme.BASE)
                    .replace("__NAV__", theme.nav(_NAV_LANDING))
                    .replace("__TOTAL__", f"{total:,}")
                    .replace("__REPO__", REPO)
                    .replace("__STAGE__", _stage(stage_names)))


def build(resume, out_dir: Path, count: int = 24) -> Path:
    """Emit the whole static site into `out_dir`: a landing page, the embedded
    whole-space browser, and the handful of hero previews the landing shows.

    Everything is static — no server, no build step for the visitor. Returns the
    landing page path.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # A clean build: drop any pages from a previous run (e.g. a different hero set)
    # so the output is exactly what this build produced.
    for stale in out_dir.glob("*.html"):
        stale.unlink()

    data = bake(resume)
    (out_dir / "browse.html").write_text(
        viewer.page(space.spread(count), resume, preview="embed",
                    pages=space.pages(count), markups=data["markups"],
                    css=data["css"], count=count, topbar=theme.nav(_NAV_BROWSE)),
        encoding="utf-8")

    # A curated, colourful trio for the hero, each a real render written beside the page.
    hero = HERO_SPECS
    for spec in hero:
        (out_dir / f"{spec.name}.html").write_text(
            compose.render(resume, spec), encoding="utf-8")

    index = out_dir / "index.html"
    index.write_text(landing(space.TOTAL, [s.name for s in hero]), encoding="utf-8")
    return index
