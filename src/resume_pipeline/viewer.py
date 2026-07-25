"""The one viewer: a grid of live layout previews.

There used to be two of these — a static catalogue and a served explorer — rendering
the same grid of the same scaled iframes. They drifted, as duplicated UI does. This is
the single implementation (ADR-0004), parameterised by the two things that actually
differ between deliveries:

- **where previews come from** — a `/preview/` route on a running server, or the baked
  `markups`/`css` tables reassembled in the browser (see `bake`);
- **whether the page can act** — a served page can export a PDF and publish; a static
  one cannot, so those controls are absent rather than present and broken.

Everything else is identical, and a test asserts that: normalise those two switches
and the two deliveries are byte-equal. **Keep it that way.** A third mode used to
exist — `preview="file"`, a fixed 21-layout sample with no filters at all — and it was
the one place a bug could hide from every other delivery, which is exactly what
happened. It is gone: anything static is now `embed`, which browses and filters the
whole space with no backend, so both deliveries are the same product.

Previews are HTML in scaled iframes, never pre-rendered images. They are therefore
*live* — what you see is what publishes, and a catalogue costs milliseconds to build
rather than a second per variant.
"""
from __future__ import annotations

import html
import json
import re

from . import compose, space, theme

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
    """The two lookup tables plus the constant title, enough to rebuild every preview
    in the browser — which is what `preview="embed"` runs on.

    A rendered layout separates cleanly: its `<body>` depends only on
    (header, skills, promo, grouping) — **120** — and its `<style>` only on
    (palette, typeface, density, header==band) — **168**. So 288 renders cover all
    10,080 layouts. `test_viewer.py` proves the reassembly is byte-identical to
    `compose.render`; that invariant is the only reason a static delivery can browse
    the whole space with no backend.

    Renders 120 bodies and calls `compose.css` 168 times — not the whole space —
    because the invariant lets each table be filled from a single representative.
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


def rebuild(spec: compose.Spec, data: dict) -> str:
    """Reassemble one preview from the baked tables — the Python mirror of the
    viewer's `previewDoc()`. Exists so a test can hold the two renderers to
    byte-equality; the browser runs the JS version of exactly this.

    Equals `compose.render(resume, spec)` for every one of the 10,080 specs, up to the
    newline `render` writes *after* `</html>` — whitespace outside the root element,
    which no parser sees. `_BODY` captures up to `</body></html>`, so neither this nor
    the JS reproduces it.
    """
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>'
            + data["title"] + ' - Resume</title><style>' + data["css"][css_key(spec)]
            + '</style></head><body>' + data["markups"][markup_key(spec)]
            + '</body></html>')


def axes_of(spec: compose.Spec) -> dict[str, str]:
    """The spec's axis values, keyed by axis name — the facets, and the chips."""
    return {
        "palette": compose.PALETTES[spec.palette][0],
        "typeface": compose.TYPEFACES[spec.typeface][0],
        "header": spec.header,
        "skills": spec.skills,
        "promo": spec.promo,
        "density": compose.DENSITIES[spec.density][0],
        "grouping": spec.grouping,
    }


def describe(spec: compose.Spec) -> dict:
    """A spec as the page (and an agent reading `options.json`) sees it."""
    return {
        "name": spec.name,
        "description": spec.description,
        "axes": axes_of(spec),
    }


def page(specs, resume, *, preview: str = "route", exportable: bool = False,
         pages: int = 0, markups: dict | None = None, css: dict | None = None,
         count: int = 24, topbar: str = "", footer: str = "") -> str:
    """Render the viewer.

    `preview` is one of the two deliveries:
    - "route" — previews come from `/preview/<name>` on a running server, which also
                pages and filters; this delivery can export and publish;
    - "embed" — no server: the whole space is enumerated, filtered and paged in the
                browser, and every preview is rebuilt from the baked `markups`/`css`
                tables. Used by both static outputs — the hosted demo and the local
                `catalogue`. `markups`/`css` come from `bake`; `count` is the page size.

    `topbar`/`footer` are the chrome around the app. Every delivery passes them, so
    the viewer you run locally and the one you link to are the same product — but the
    *content* differs, because what is honest differs: the hosted demo's bar links to
    a front door and an overview, and a local one cannot (there is no landing page on
    your machine), so `theme.local_nav` gives the same band a non-linking wordmark and
    captions it with the profile instead. Both are markup rather than a flag, so this
    module never has to know what either bar says.
    """
    # Two deliveries, and only two (ADR-0004). A third mode is how the last one grew
    # a lesser variant nothing tested, so an unknown one is an error rather than a
    # page that renders and quietly does half of what it should.
    if preview not in ("route", "embed"):
        raise ValueError(f"unknown delivery {preview!r}: expected 'route' or 'embed'")
    if preview == "embed" and not (markups and css):
        raise ValueError("preview='embed' needs the baked markups/css from bake()")

    options = [describe(s) for s in specs]
    title = html.escape(resume.name or "Resume")
    # Palette is one axis, and the first segment of every spec name — so the
    # viewer can offer "this layout, that colour" as an instant re-render of a
    # neighbouring spec rather than a live edit. The swatch colour is the accent.
    palettes = [{"name": p[0], "accent": p[1]} for p in compose.PALETTES]
    # Typeface is the same story on the second name segment: a small closed set, so
    # it earns its own "hold this constant" bar too — but sample chips rather than
    # swatches, each rendered in its own face, since a font can't be a dot. (RP-0037.)
    typefaces = [{"name": t[0], "font": t[1]} for t in compose.TYPEFACES]
    # Every axis, with the values it can be filtered to. One structure so the
    # dropdowns, the card chips and the query string cannot disagree about what
    # an axis is called or which values it has (RP-0033).
    axes_meta = []
    for key, label in (("palette", "Color"), ("typeface", "Type"),
                       ("header", "Header"), ("skills", "Skills"),
                       ("promo", "Promo"), ("density", "Density"),
                       ("grouping", "Group")):
        entry = {"key": key, "label": label, "values": space.axis_values(key)}
        if key == "typeface":
            # Body and display faces differ on `mixed` alone, and that difference is
            # the only thing distinguishing it from `charter` — so a sample has to
            # show both. (Both resolve per machine until RP-0041 lands.)
            entry["fonts"] = {t[0]: {"body": t[1], "display": t[2]}
                              for t in compose.TYPEFACES}
        axes_meta.append(entry)
    # The footer carries its own measure wrapper, so an absent one leaves no empty box.
    foot = f'<div class="wrap foot">{footer}</div>' if footer else ""
    return _PAGE.replace("__KIT__", theme.TOKENS + theme.BASE) \
                .replace("__TOPBAR__", topbar) \
                .replace("__FOOTER__", foot) \
                .replace("__PAGES__", str(pages)) \
                .replace("__AXES__", json.dumps(axes_meta)) \
                .replace("__TITLE_JS__", json.dumps(compose.esc(resume.name))) \
                .replace("__TITLE__", title) \
                .replace("__TOTAL__", f"{space.TOTAL:,}") \
                .replace("__TOTAL_N__", str(space.TOTAL)) \
                .replace("__PREVIEW__", preview) \
                .replace("__EXPORTABLE__", "true" if exportable else "false") \
                .replace("__COUNT__", str(count)) \
                .replace("__PALETTES__", json.dumps(palettes)) \
                .replace("__TYPEFACES__", json.dumps(typefaces)) \
                .replace("__MARKUPS__", json.dumps(markups) if markups else "null") \
                .replace("__CSS__", json.dumps(css) if css else "null") \
                .replace("__OPTIONS__", json.dumps(options))


# The page is one string with a handful of substitutions rather than a template
# engine: it is the only page, it has no dependencies, and it has to work equally
# from `file://` and from the server.
_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__ — Layouts</title>
<style>
  /* Design kit (tokens + shared components) lives in theme.py; the landing and this
     viewer both draw from it, so the two surfaces are one system. Committed dark. */
__KIT__
  html,body{margin:0}
  body{background:var(--bg);color:var(--ink);font-family:var(--font-body);font-size:14px;line-height:1.5}

  /* ── The intro ───────────────────────────────────────────────────────────
     The page opens like a page of the site — eyebrow, headline, lede — and that
     block scrolls away, leaving only the control bar stuck to the top. It is the
     onboarding copy the old header had to carry in its gutter, given somewhere to
     live where it costs the working view nothing. */
  .intro{padding:38px 0 26px}
  .intro h1{font-size:34px;line-height:1.08;font-weight:800;letter-spacing:-.02em;
            margin:17px 0 12px}
  .lede{color:var(--muted);font-size:15.5px;max-width:62ch;margin:0}
  .lede b{color:var(--ink);font-weight:500}
  .hint{margin:13px 0 0;color:var(--muted);font-size:13.5px;max-width:74ch;
        border-left:2px solid var(--line2);padding-left:14px}
  /* A quiet text-weight toggle for the fuller explanation — a returning reader
     doesn't need it, so it starts closed and the choice persists. */
  .hintbtn{margin-top:14px;padding:2px 0;background:none;border:0;
           color:var(--muted);font-size:13px;text-decoration:underline;
           text-underline-offset:3px;cursor:pointer}
  .hintbtn:hover{color:var(--accent)}

  /* ── The control bar ─────────────────────────────────────────────────────
     A full-bleed band that sticks once the intro has scrolled past, with its
     content on the page measure so the filters share the grid's left edge. The
     site nav scrolls away (static) so this is the only sticky element — no
     two-sticky overlap. Blurred ground, matching the nav's treatment. */
  .sitenav{position:static}
  header{position:sticky;top:0;z-index:20;border-top:1px solid var(--line);
         border-bottom:1px solid var(--line);
         background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(12px)}
  .bar{display:flex;flex-direction:column;gap:10px;padding-top:12px;padding-bottom:12px}
  /* Colour and the dropdowns sit side by side on one line and share a baseline.
     They stay separate containers so that when the line is too narrow the whole
     dropdown group drops below the swatches — a wrap can never interleave a
     swatch with a pill (RP-0043). */
  .filters{display:flex;flex-wrap:wrap;align-items:center;gap:9px 20px}
  /* Status line: the live count on the left, the pager opposite. Wraps as a whole
     when it must, so the pager drops to its own line intact rather than crushing. */
  .status{display:flex;align-items:center;gap:6px 14px;flex-wrap:wrap}
  .meta{color:var(--muted);font-size:12.5px}
  .navwrap{display:flex;align-items:center;gap:14px;margin-left:auto}
  /* The count/holds text yields so the four nav controls never wrap (RP-0043,
     regression-checklist row 9): pair min-width:0 here with flex-shrink:0 on .nav. */
  #pageMeta{min-width:0}
  .nav{display:flex;gap:6px;align-items:center;flex-shrink:0}
  .nav button{padding:5px 11px}

  /* Buttons (Open / Copy / pager / dialog) come from the shared kit — same system
     as the landing's CTAs. Only the app-specific controls below override it. */

  /* ── Filtering (RP-0033) ─────────────────────────────────────────────────
     Every axis holds a set: empty is unconstrained, several values are an OR,
     axes combine with AND. Colour keeps swatches because a swatch *is* the
     value; the rest are dropdowns, since they are words either way. */
  .brk{flex-basis:100%;width:100%;height:0;margin:0;padding:0;border:0}
  .lbl{font-size:12px;color:var(--muted)}
  .sw{width:20px;height:20px;border-radius:50%;border:2px solid transparent;padding:0;
      cursor:pointer;background-clip:padding-box;
      transition:transform .12s,box-shadow .12s,border-color .12s}
  /* Hover is neutral and selection is the accent — sharing one colour made
     "might click" and "did click" identical. */
  .sw:hover{transform:scale(1.15);box-shadow:0 0 0 2px var(--card),0 0 0 3px var(--muted)}
  .sw.on{border-color:var(--ink);box-shadow:0 0 0 2px var(--card),0 0 0 3px var(--ink)}
  .fpill{font:inherit;font-size:12.5px;font-weight:500;line-height:1;
         padding:7px 13px;border-radius:20px;background:var(--btn);
         border:1px solid var(--btn-line);cursor:pointer;color:var(--ink);
         display:inline-flex;align-items:center;gap:7px;white-space:nowrap;
         transition:border-color .12s,background .12s,color .12s}
  .fpill:hover:not(:disabled){border-color:var(--muted);color:var(--ink)}
  .fpill.on{border-color:var(--accent);color:var(--accent);font-weight:600;
            background:color-mix(in srgb,var(--accent) 12%,transparent)}
  .fpill.live{border-color:var(--muted)}
  .ct{font-size:10.5px;font-weight:700;background:var(--accent);color:var(--card);
      border-radius:9px;padding:1px 6px;min-width:16px;text-align:center;
      font-family:ui-monospace,Menlo,monospace}
  .caret{font-size:9px;opacity:.55}
  .clearbtn{background:none;border-color:transparent;color:var(--muted);padding:7px 10px}
  .clearbtn:hover:not(:disabled){border-color:var(--muted);color:var(--ink)}
  .clearbtn:disabled,.vchip:disabled{opacity:.34;cursor:default}
  .clearbtn:disabled:hover{border-color:transparent}
  .vchip{font-size:11.5px;line-height:1;padding:4px 10px;border-radius:20px;background:none;
         border:1px solid transparent;cursor:pointer;color:var(--muted);
         display:inline-flex;align-items:center;gap:5px}
  .vchip:hover:not(:disabled){border-color:var(--muted);color:var(--ink)}
  .x{font-size:11px;opacity:.8}

  .pop{position:absolute;z-index:60;background:var(--card);border:1px solid var(--line);
       border-radius:12px;padding:13px 15px;box-shadow:var(--shadow);max-width:min(560px,92vw)}
  .poptitle{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);
            font-weight:700;margin-bottom:9px;display:flex;gap:9px;align-items:center}
  .axvals{display:flex;flex-wrap:wrap;gap:6px}
  .val{display:flex;flex-direction:column;align-items:center;gap:5px;padding:7px 8px 6px;
       border-radius:9px;border:1px solid var(--btn-line);background:var(--btn);
       cursor:pointer;color:var(--ink);width:68px;
       transition:border-color .12s,background .12s}
  .val:hover{border-color:var(--muted)}
  .val.on{border-color:var(--accent);background:color-mix(in srgb,var(--accent) 12%,transparent)}
  .val .cap{font-size:10.5px;line-height:1.2;color:var(--muted)}
  .val.on .cap{color:var(--accent);font-weight:650}

  /* The icons depict a printed page — always white stock, always dark ink — so
     their palette is fixed and does not follow the UI theme. */
  .thumb{--ic:#0b6fa4;width:46px;height:31px;background:#fff;border:1px solid #d7dce4;
         border-radius:3px;padding:4px;display:flex;flex-direction:column;gap:2px;
         overflow:hidden}
  .t-type{align-items:center;justify-content:center;gap:0}
  .t-hr{height:1px;width:78%;background:#d7dce4;margin:2.5px 0;flex:none}
  .t-l{height:2px;border-radius:1px;background:#d7dce4;flex:none}
  .t-f{height:2px;border-radius:1px;background:#eaedf2;flex:none}
  .t-a{height:3px;border-radius:1px;background:var(--ic);flex:none}
  .t-row{display:flex;gap:3px;align-items:center;flex:none}
  .t-pill{height:4.5px;border-radius:3px;background:var(--ic);opacity:.65;flex:1}
  .t-blk{height:6px;border-radius:1px;background:var(--ic);opacity:.34;flex:1}
  .t-rule{height:2.6px;border-radius:1px;background:var(--ic);flex:none}
  .t-band{background:#14181f;margin:-4px -4px 0;padding:4px;display:flex;
          flex-direction:column;gap:2px;flex:none}
  .t-band .t-w{height:3.4px;border-radius:1px;background:#fff;width:62%}
  .t-band .t-w2{height:2px;border-radius:1px;background:#fff;opacity:.55;width:80%}
  .t-sp{flex:1}

  /* The grid rides the page measure, like everything else on the site. `.card` is
     the kit's surface — only the parts a preview card needs beyond it are here. */
  .grid{display:grid;gap:22px;padding:26px 0 40px;
        grid-template-columns:repeat(auto-fill,minmax(270px,1fr))}
  .foot{padding-bottom:56px}
  .card{overflow:hidden;display:flex;flex-direction:column;
        transition:border-color .14s,transform .14s,box-shadow .14s}
  .card:hover{transform:translateY(-3px);border-color:var(--line2);
              box-shadow:0 1px 2px rgba(0,0,0,.5),0 20px 44px rgba(0,0,0,.55)}

  /* A real 8.5in-wide render, scaled down — not a screenshot. What you see here is
     exactly what publishes. An aspect ratio rather than a fixed height, so every
     card shows the same *fraction* of the page whatever width the column ends up. */
  .shot{position:relative;aspect-ratio:816/1010;overflow:hidden;background:#fff;cursor:pointer;
        border-bottom:1px solid var(--line)}
  .shot iframe{position:absolute;top:0;left:0;width:816px;height:1056px;border:0;
               transform-origin:top left;pointer-events:none}
  .shot .veil{position:absolute;inset:0}

  /* Cards in a row are as tall as the tallest, and chip rows wrap to different
     heights — so the actions are pinned to the bottom rather than floating
     wherever the chips happen to end. */
  .info{padding:13px 14px 14px;display:flex;flex-direction:column;gap:11px;flex:1}
  .chips{display:flex;flex-wrap:wrap;gap:5px}
  .chip{font:inherit;font-size:10.5px;background:var(--bg);border:1px solid var(--line);
        border-radius:20px;padding:2px 8px;color:var(--muted);cursor:pointer;
        transition:border-color .12s,background .12s,color .12s}
  .chip:hover:not(:disabled){border-color:var(--muted);color:var(--ink)}
  .chip.on{border-color:var(--accent);color:var(--accent);font-weight:650;
           background:color-mix(in srgb,var(--accent) 12%,transparent)}
  .chip:disabled{cursor:default}
  /* Pinned to the bottom: cards in a row are as tall as the tallest, and chip
     rows wrap to different heights, so without this the buttons sit at a
     different height on every card. */
  .acts{display:flex;gap:7px;margin-top:auto;padding-top:2px}
  .acts button{flex:1;padding:7px 0;font-size:12.5px}

  dialog{border:0;border-radius:14px;padding:0;background:var(--card);color:var(--ink);
         width:min(94vw,900px);box-shadow:var(--shadow)}
  dialog::backdrop{background:rgba(8,10,14,.55)}
  /* No wrapping: a long spec name used to push Close onto a line of its own,
     which is where it went to hide. The name truncates instead. */
  .dlg-bar{display:flex;align-items:center;gap:10px;padding:11px 14px;
           border-bottom:1px solid var(--line);flex-wrap:nowrap}
  .dlg-id{min-width:0;flex:1;display:flex;flex-direction:column;gap:1px}
  .dlg-id b{font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .dlg-id .meta{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .dlg-acts{display:flex;gap:8px;flex:0 0 auto}
  dialog iframe{width:100%;height:min(76vh,1056px);border:0;background:#fff}
  /* With a dialog open, reaching the bottom of the preview handed the scroll
     back to the grid behind it. Lock the page while the modal is up. */
  body.modal-open{overflow:hidden}

  /* One group, two containers (RP-0043). Colour keeps its own chrome — a swatch
     *is* the value, which no label improves on — and the six dropdowns sit beside
     it. They stay separate containers rather than one concatenated bar, because a
     single bar interleaves swatches and pills the moment it wraps; here the whole
     dropdown group drops to the next line instead. Multi-select throughout — two
     swatches are an OR. */
  .palette{display:flex;align-items:center;gap:8px;margin:0;flex-wrap:wrap}
  /* Label + swatches move as one: a wrap that split them would read as two
     controls, and balanceWrap counts children, so this must be a single item. */
  .swgroup{display:inline-flex;align-items:center;gap:7px}
  .palette .lbl{font-size:12px;color:var(--muted)}

  .toast{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);
         background:var(--ink);color:var(--bg);padding:9px 16px;border-radius:8px;
         font-size:13px;opacity:0;transition:opacity .2s;pointer-events:none;z-index:60}
  .toast.show{opacity:1}
  /* ── Narrow ──────────────────────────────────────────────────────────────
     The control bar needs no restructuring — `.filters` already drops the dropdown
     group below the swatches on its own. Only the intro's display type has to come
     down, or a 34px headline eats the first screen.
     Kept at the END of the sheet deliberately, so these win the cascade against
     the rules they override regardless of where those are declared. */
  @media (max-width:900px){
    .intro{padding:28px 0 20px}
    .intro h1{font-size:26px}
    .lede{font-size:14.5px}
    .grid{gap:16px}
  }
</style></head><body>
__TOPBAR__
<!-- The intro is page content, not chrome: it scrolls away and leaves the control
     bar alone at the top. The profile's name is the eyebrow rather than an <h1> —
     the subject of this page is the space, not the person in the sample. -->
<section class="intro">
  <div class="wrap">
    <span class="pill"><b></b>Layout browser · __TITLE__</span>
    <h1>__TOTAL__ layouts, one profile.</h1>
    <p class="lede">Every card below is a <b>live render</b> of the same profile — not a
      screenshot, and exactly what publishes. Hold a <b>colour</b> or <b>typeface</b> to keep it
      constant while you judge the rest, page through the space, and open any layout full size.</p>
    <button class="hintbtn" id="hintBtn" aria-expanded="false" aria-controls="hint">What is this?</button>
    <p class="hint" id="hint" hidden>Layouts are <b>generated</b>, not templates — each is one combination of
    seven independent choices, so there are __TOTAL__ of them. The arrows walk the space in
    order; <b>Shuffle</b> jumps somewhere else entirely. Pick a <b>colour</b> or <b>typeface</b>
    to hold it constant while you judge the rest. Open any layout, then <b>Make this my resume</b>
    to publish it — every preview is a live render, identical to what gets published.</p>
  </div>
</section>

<!-- The control bar: filters on one line, the live count and the pager on the next.
     Sticks to the top once the intro is past, so it is the only thing competing with
     the grid for the working view. `#pop` stays a child of the sticky element — it is
     positioned against it. -->
<header>
  <div class="wrap bar">
    <div class="filters">
      <div class="palette" id="palette"></div>
      <div class="palette" id="axes"></div>
    </div>
    <div class="status">
      <span class="meta" id="meta"></span>
      <span class="navwrap">
        <span class="meta" id="pageMeta"></span>
        <span class="nav" id="nav" hidden>
          <button id="first" title="Back to page 1">«</button>
          <button id="prev" title="Previous page">‹</button>
          <button id="shuffle">Shuffle</button>
          <button id="next" title="Next page">›</button>
        </span>
      </span>
    </div>
  </div>
  <div class="pop" id="pop" hidden></div>
</header>

<main class="wrap"><div class="grid" id="grid"></div></main>

<dialog id="dlg">
  <div class="dlg-bar">
    <div class="dlg-id">
      <b id="dlgName"></b>
      <span class="meta" id="dlgDesc"></span>
    </div>
    <div class="dlg-acts">
      <button id="dlgCopy">Copy Name</button>
      <button id="dlgExport" hidden>Export PDF</button>
      <button id="dlgPublish" class="primary" hidden>★ Make this my resume</button>
      <button id="dlgClose">Close</button>
    </div>
  </div>
  <iframe id="dlgFrame" title="preview"></iframe>
</dialog>

__FOOTER__
<div class="toast" id="toast"></div>

<script>
let   OPTIONS    = __OPTIONS__;
let   PAGES      = __PAGES__;   // updated as filtering narrows the set
let   PAGE_INDEX = 0;
const PREVIEW    = "__PREVIEW__";
const EXPORTABLE = __EXPORTABLE__;
let   TOTAL      = __TOTAL_N__;       // the *filtered* layout count, a number
const SPACE_TOTAL = __TOTAL_N__;      // the whole space, for "N of TOTAL"
const PALETTES   = __PALETTES__;
const TYPEFACES  = __TYPEFACES__;
const ACCENT     = Object.fromEntries(PALETTES.map(p => [p.name, p.accent]));
const AXES       = __AXES__;
// One set per axis. Empty means unconstrained; several values mean OR within that
// axis; axes combine with AND. A "hold" is now just a selection of size one, so
// RP-0037's colour/type holds are the same mechanism as every other facet.
const FILTERS    = Object.fromEntries(AXES.map(a => [a.key, new Set()]));
const ACTIVE     = () => AXES.reduce((n, a) => n + FILTERS[a.key].size, 0);
let   OPEN_AXIS  = null;   // which dropdown is showing, if any

const $ = s => document.querySelector(s);
const previewUrl = name => "/preview/" + encodeURIComponent(name);

// Two deliveries, and this is the only thing that separates them (ADR-0004):
// "route" asks a server for each page and each preview; "embed" has no server, so
// it enumerates, filters and pages the whole space in the browser and rebuilds every
// preview from the baked markup/CSS tables. Both browse all 10,080 and both filter —
// there is no third, lesser mode.
const EMBED = PREVIEW === "embed";

// ── Embedded demo: the whole space, no backend ─────────────────────────────
// MARKUPS[header|skills|promo|grouping] -> <body> HTML   (120)
// CSSTAB [palette|typeface|density|band] -> <style> CSS  (168)
// Proven to reassemble render(spec) exactly for all 10,080 specs (see demo.py),
// so this is the one renderer's output, not a second renderer.
const MARKUPS = __MARKUPS__;
const CSSTAB  = __CSS__;
// The preview's <title>, escaped exactly as compose.render escapes it — NOT the page
// title above, whose "Resume" fallback would make a nameless profile's preview differ
// from the real render. viewer.rebuild() is the Python mirror of previewDoc() below.
const DEMO_TITLE = __TITLE_JS__;
const COUNT = __COUNT__;                       // layouts per page
const _AXORDER = ["palette","typeface","header","skills","promo","density","grouping"];
const PIDX = EMBED ? Object.fromEntries(PALETTES.map((p,i)=>[p.name,i])) : null;
const TIDX = EMBED ? Object.fromEntries(TYPEFACES.map((t,i)=>[t.name,i])) : null;
const DIDX = EMBED ? Object.fromEntries(AXES.find(a=>a.key==="density").values.map((v,i)=>[v,i])) : null;

let SPACE = [];   // every spec, in a stable, well-mixed order
function _fnv(s){ let h=2166136261>>>0; for(let i=0;i<s.length;i++){ h^=s.charCodeAt(i); h=Math.imul(h,16777619);} return h>>>0; }
function buildSpace(){
  const vals = Object.fromEntries(AXES.map(a=>[a.key, a.values]));
  let combos = [{}];
  for(const k of _AXORDER){ const nx=[]; for(const c of combos) for(const v of vals[k]) nx.push({...c,[k]:v}); combos=nx; }
  SPACE = combos.map(ax => ({name:_AXORDER.map(k=>ax[k]).join("-"), axes:ax}));
  // Enumeration groups near-identical layouts; mix by a hash of the name so a page
  // shows range, not seven shades of one design. Deterministic: page 3 is page 3.
  SPACE.sort((a,b)=>_fnv(a.name)-_fnv(b.name));
}
function _matchesEmbed(axes){ return AXES.every(a=>{ const s=FILTERS[a.key]; return !s.size || s.has(axes[a.key]); }); }
function _describe(ax){ return `${ax.palette} · ${ax.typeface} · ${ax.header} header · ${ax.skills} skills · ${ax.promo} promo · ${ax.density} · ${ax.grouping}`; }
function embedPage(index){
  const pool = ACTIVE() ? SPACE.filter(s=>_matchesEmbed(s.axes)) : SPACE;
  const total = pool.length;
  const pages = Math.max(1, Math.ceil(total / COUNT));
  const i = ((index % pages) + pages) % pages;
  const options = pool.slice(i*COUNT, i*COUNT + COUNT)
                      .map(s => ({name:s.name, axes:s.axes, description:_describe(s.axes)}));
  return {options, index:i, pages, total};
}
// Rebuild a preview from the baked tables — the HTML render() would have produced,
// assembled in the browser instead of fetched from /preview.
function previewDoc(ax){
  const mk = [ax.header, ax.skills, ax.promo, ax.grouping].join("|");
  const ck = [PIDX[ax.palette], TIDX[ax.typeface], DIDX[ax.density], ax.header==="band"?"1":"0"].join("|");
  return '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>'
       + DEMO_TITLE + ' - Resume</title><style>' + CSSTAB[ck] + '</style></head><body>'
       + MARKUPS[mk] + '</body></html>';
}

// Flex wraps greedily — it packs the first line and drops the remainder, so six
// pills break 5+1. There is no CSS for balanced wrapping, so measure and insert
// explicit breaks: the fewest rows that fit, split as evenly as those rows allow.
function balanceWrap(box){
  if(!box) return;
  box.querySelectorAll(".brk").forEach(b => b.remove());
  const items = [...box.children];
  if(items.length < 2) return;
  const cs = getComputedStyle(box), gap = parseFloat(cs.columnGap || cs.gap) || 0;
  const W = box.clientWidth, w = items.map(i => i.getBoundingClientRect().width);
  const lineW = a => a.reduce((x, y) => x + y, 0) + gap * (a.length - 1);
  if(lineW(w) <= W + 0.5) return;
  for(let rows = 2; rows <= items.length; rows++){
    const base = Math.floor(items.length / rows), rem = items.length % rows;
    const sizes = Array.from({length: rows}, (_, i) => base + (i < rem ? 1 : 0));
    let ok = true, at = 0;
    for(const sz of sizes){ if(lineW(w.slice(at, at + sz)) > W){ ok = false; break } at += sz }
    if(ok){
      at = 0;
      for(let i = 0; i < sizes.length - 1; i++){
        at += sizes[i];
        const br = document.createElement("span"); br.className = "brk";
        box.insertBefore(br, items[at]);
      }
      return;
    }
  }
}

function toggleFilter(axis, value){
  const set = FILTERS[axis];
  set.has(value) ? set.delete(value) : set.add(value);
  goto(0);                      // a changed filter is a different browse: start at its first page
}
function clearAxis(axis){ if(FILTERS[axis].size){ FILTERS[axis].clear(); goto(0); } }
function clearAll(){ if(ACTIVE()){ AXES.forEach(a => FILTERS[a.key].clear()); goto(0); } }

let toastTimer;
function toast(msg){
  const t = $("#toast"); t.textContent = msg; t.classList.add("show");
  clearTimeout(toastTimer); toastTimer = setTimeout(()=>t.classList.remove("show"), 1900);
}

function copy(name){
  navigator.clipboard.writeText(name).then(()=>toast("Copied: " + name),
                                           ()=>toast("Could not copy"));
}

function fitShot(frame){
  // Scale the 816px-wide render to whatever width the card ended up being.
  const w = frame.parentElement.clientWidth;
  frame.style.transform = `scale(${w/816})`;
}

let cursor = 0;
let CURRENT = null;   // the spec currently open in the dialog

// The explainer is pure onboarding and the tallest thing in the header, so it starts
// *minimised* — one quiet "What is this?" link — and only opens if asked. The choice
// then persists either way, so a reader who opened it keeps it open.
const HINT_KEY = "resume-pipeline:hint-hidden";
function setHint(hidden){
  $("#hint").hidden = hidden;
  const b = $("#hintBtn");
  b.textContent = hidden ? "What is this?" : "Hide";
  b.setAttribute("aria-expanded", String(!hidden));
}
// Hidden by default: shown only if the reader explicitly opened it before ("0").
try{ setHint(localStorage.getItem(HINT_KEY) !== "0"); }catch(e){ setHint(true); }
$("#hintBtn").addEventListener("click", () => {
  const hidden = !$("#hint").hidden;
  setHint(hidden);
  try{ localStorage.setItem(HINT_KEY, hidden ? "1" : "0"); }catch(e){}
});

function render(){
  drawFilters();
  // The count follows the filters: narrow an axis and "10,080 layouts" becomes the
  // size of that subset. The controls already say *what* is filtered, so repeating
  // it here would be redundant — this says only how much (RP-0033/0035).
  $("#meta").textContent = ACTIVE()
    ? `${TOTAL.toLocaleString()} of ${SPACE_TOTAL.toLocaleString()} layouts`
    : `${TOTAL.toLocaleString()} layout${TOTAL===1?"":"s"}`;
  $("#nav").hidden = PAGES <= 1;
  $("#pageMeta").textContent =
    PAGES > 1 ? `page ${PAGE_INDEX + 1} of ${PAGES.toLocaleString()}` : "";
  $("#first").disabled = PAGE_INDEX === 0;   // already home
  const grid = $("#grid");
  grid.innerHTML = "";
  OPTIONS.forEach((v, i) => {
    const name = v.name;
    const axes = v.axes;
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <div class="shot"><iframe loading="lazy"
           title="${name}" scrolling="no"></iframe><div class="veil"></div></div>
      <div class="info">
        <div class="chips">${Object.entries(axes).map(([ax, val]) =>
          `<button class="chip${FILTERS[ax] && FILTERS[ax].has(val) ? " on" : ""}"
                   data-ax="${ax}" data-v="${val}"
                   title="Filter to ${val}">${val}</button>`).join("")}</div>
        <div class="acts">
          <button class="o">Open</button>
          <button class="c">Copy Name</button>
        </div>
      </div>`;
    const frame = card.querySelector("iframe");
    if(EMBED) frame.srcdoc = previewDoc(axes); else frame.src = previewUrl(name);
    frame.addEventListener("load", ()=>fitShot(frame));
    new ResizeObserver(()=>fitShot(frame)).observe(card.querySelector(".shot"));
    card.querySelector(".shot").onclick = ()=>{ cursor=i; open(v); };
    card.querySelector(".o").onclick = ()=>{ cursor=i; open(v); };
    card.querySelector(".c").onclick = ()=>copy(name);
    // A chip is the fastest route into a filter: you are looking at a layout you
    // like, and "more like this one" starts here rather than in the header.
    card.querySelectorAll(".chips .chip").forEach(chip =>
      chip.onclick = ()=>toggleFilter(chip.dataset.ax, chip.dataset.v));
    grid.appendChild(card);
  });
}

// Every value control depicts what it does. Typeface already did — a chip set in
// its own face — and the rest follow: a schematic of the treatment, abstract on
// purpose. Enough to tell `band` from `masthead`; deliberately not a second
// renderer to keep in step with compose.py.
function icon(axis, value){
  const t = document.createElement("span"); t.className = "thumb";
  const L = (w, cls) => { const l = document.createElement("span");
    l.className = cls || "t-l"; if(w) l.style.width = w; return l; };
  const row = (...kids) => { const r = document.createElement("span");
    r.className = "t-row"; kids.forEach(k => r.append(k)); return r; };
  const sp = h => { const e = document.createElement("span");
    e.style.cssText = h ? `height:${h};flex:none` : "flex:1"; return e; };

  if(axis === "typeface"){
    const f = (AXES.find(a => a.key === "typeface").fonts || {})[value] || {};
    t.classList.add("t-type");
    const mk = (size, weight, colour, fam) => { const e = document.createElement("span");
      e.textContent = "Rag";
      e.style.cssText = `font:${weight} ${size}px/1.05 ${fam || "inherit"};color:${colour}`;
      return e; };
    // Same glyphs in both rows so the face is the only variable: `charter` is one
    // face throughout, `mixed` is a serif display over a sans body.
    const hr = document.createElement("span"); hr.className = "t-hr";
    t.append(mk(12.5, 600, "#12151a", f.display), hr, mk(11, 400, "#3d444e", f.body));
    return t;
  }
  if(axis === "header"){
    if(value === "band"){ const b = document.createElement("span"); b.className = "t-band";
      const w1 = document.createElement("span"); w1.className = "t-w";
      const w2 = document.createElement("span"); w2.className = "t-w2";
      b.append(w1, w2); t.append(b, L("85%"), L("62%", "t-f")); }
    if(value === "masthead"){ const n = L("58%", "t-a"); n.style.alignSelf = "center";
      const r = L("74%"); r.style.alignSelf = "center";
      t.append(n, r, L("90%", "t-f"), L("70%", "t-f")); }
    if(value === "rule") t.append(L("50%", "t-a"), L("100%", "t-rule"), L("88%", "t-f"), L("66%", "t-f"));
    if(value === "split"){ const a = L("100%", "t-a"); a.style.flex = "1.3";
      const c = L("100%"); c.style.flex = "1";
      t.append(row(a, c), L("100%"), L("84%", "t-f"), L("62%", "t-f")); }
    if(value === "minimal") t.append(L("46%", "t-a"), sp(), L("88%", "t-f"), L("70%", "t-f"));
    return t;
  }
  if(axis === "skills"){
    const many = (n, cls) => { const w = document.createElement("span"); w.className = "t-row";
      for(let i = 0; i < n; i++){ const q = document.createElement("span"); q.className = cls; w.append(q) }
      return w; };
    if(value === "pills") t.append(L("34%", "t-f"), many(3, "t-pill"), many(3, "t-pill"));
    if(value === "inline") t.append(L("34%", "t-f"), L("96%"), L("90%"), L("74%"));
    if(value === "grid") t.append(L("34%", "t-f"), many(2, "t-blk"), many(2, "t-blk"));
    return t;
  }
  if(axis === "promo"){
    if(value === "ladder"){ ["34%", "46%", "58%"].forEach((w, i) =>
        t.append(row(sp((i * 5) + "px"), L(w, "t-a")))); t.append(L("80%", "t-f")); }
    if(value === "badge"){ const bg = document.createElement("span"); bg.className = "t-pill";
      bg.style.cssText += ";flex:0 0 13px;opacity:.85";
      t.append(row(L("52%", "t-a"), bg), L("92%", "t-f"), L("74%", "t-f"), L("60%", "t-f")); }
    if(value === "stacked") t.append(L("58%", "t-a"), L("46%", "t-a"), L("92%", "t-f"), L("72%", "t-f"));
    if(value === "inline") t.append(row(L("100%", "t-a"), L("100%")), L("90%", "t-f"), L("70%", "t-f"));
    return t;
  }
  if(axis === "density"){
    t.style.gap = ({airy: 5, normal: 3, compact: 1.2}[value] || 2) + "px";
    const n = {airy: 4, normal: 5, compact: 8}[value] || 4;
    for(let i = 0; i < n; i++) t.append(L((72 + ((i * 19) % 24)) + "%"));
    return t;
  }
  if(axis === "grouping"){
    if(value === "grouped"){
      const g = (a, b, c) => { const box = document.createElement("span");
        box.style.cssText = "display:flex;flex-direction:column;gap:2px";
        box.append(L(a, "t-a"), L(b), L(c)); return box; };
      t.append(g("38%", "92%", "76%"), sp("4px"), g("44%", "88%", "70%"));
    }
    if(value === "flat") for(let i = 0; i < 6; i++) t.append(L((88 - ((i * 11) % 26)) + "%"));
    return t;
  }
  return t;
}

// One verb for every reset. Always present, disabled when there is nothing to
// clear, so it never shifts the row it sits in by appearing and vanishing.
function clearBtn(axis, cls){
  const n = axis ? FILTERS[axis].size : ACTIVE();
  const b = document.createElement("button");
  b.className = cls;
  b.disabled = !n;
  b.title = n ? "Clear " + n + " selected" : "Nothing selected";
  const x = document.createElement("span"); x.className = "x"; x.textContent = "✕";
  b.append(x, document.createTextNode(axis ? "Clear" : "Clear all"));
  b.onclick = () => axis ? clearAxis(axis) : clearAll();
  return b;
}

// Colour keeps its own row and its own chrome: a swatch *is* the value, which no
// label beats. Label and swatches travel as one flex item (`.swgroup`) so a wrap
// can never split them — which is also why this row needs no balanceWrap.
function paletteBar(el){
  el.textContent = "";

  const palette = AXES.find(a => a.key === "palette");
  const group = document.createElement("span"); group.className = "swgroup";
  const lbl = document.createElement("span"); lbl.className = "lbl";
  lbl.textContent = palette.label;
  group.append(lbl);
  palette.values.forEach(v => {
    const on = FILTERS.palette.has(v);
    const b = document.createElement("button");
    b.className = "sw" + (on ? " on" : "");
    b.style.background = ACCENT[v]; b.title = v;
    b.setAttribute("aria-label", v); b.setAttribute("aria-pressed", on);
    b.onclick = () => toggleFilter("palette", v);
    group.append(b);
  });
  el.append(group);
  // Colour gets its own reset, so it is not reachable only through Clear all one
  // row down. The subtle `.vchip` -- the same per-axis clear every dropdown popover
  // carries -- not the `.clearbtn` pill, which reads as the global reset.
  el.append(clearBtn("palette", "vchip"));
}

// The other six axes are words either way, so they collapse into dropdowns on the
// row directly below colour: a fixed number of pills carrying a count, which keeps
// the header from growing with the size of the selection.
function axisBar(el){
  el.textContent = "";

  AXES.filter(a => a.key !== "palette").forEach(axis => {
    const n = FILTERS[axis.key].size, live = OPEN_AXIS === axis.key;
    const b = document.createElement("button");
    b.className = "fpill" + (n ? " on" : "") + (live ? " live" : "");
    b.append(document.createTextNode(axis.label));
    const tag = document.createElement("span");
    if(n){ tag.className = "ct"; tag.textContent = n; }
    else { tag.className = "caret"; tag.textContent = "\u25be"; }
    b.append(tag);
    b.dataset.axis = axis.key;
    b.setAttribute("aria-expanded", live);
    b.onclick = () => { OPEN_AXIS = live ? null : axis.key; drawFilters(); };
    el.append(b);
  });

  // Last: an action on everything before it. Always present, disabled when there
  // is nothing to clear, so the row never shifts as the first value is picked.
  el.append(clearBtn(null, "fpill clearbtn"));
  balanceWrap(el);
}

// A popover, not a panel: it is positioned rather than laid out, so opening a
// dropdown cannot move the header or push the grid down.
function popover(){
  const pop = $("#pop");
  if(!OPEN_AXIS){ pop.hidden = true; return; }
  const axis = AXES.find(a => a.key === OPEN_AXIS);
  pop.hidden = false;
  pop.textContent = "";
  const head = document.createElement("div"); head.className = "poptitle";
  const nm = document.createElement("span"); nm.textContent = axis.label;
  head.append(nm, clearBtn(axis.key, "vchip"));
  const vals = document.createElement("div"); vals.className = "axvals";
  axis.values.forEach(v => {
    const on = FILTERS[axis.key].has(v);
    const b = document.createElement("button");
    b.className = "val" + (on ? " on" : "");
    b.setAttribute("aria-pressed", on);
    const cap = document.createElement("span"); cap.className = "cap"; cap.textContent = v;
    b.append(icon(axis.key, v), cap);
    b.onclick = () => toggleFilter(axis.key, v);
    vals.append(b);
  });
  pop.append(head, vals);
  const btn = $("#axes").querySelector(`[data-axis="${axis.key}"]`);
  if(btn){
    const hd = $("header").getBoundingClientRect(), r = btn.getBoundingClientRect();
    pop.style.top = (r.bottom - hd.top + 8) + "px";
    const left = Math.max(14, Math.min(r.left - hd.left, hd.width - pop.offsetWidth - 14));
    pop.style.left = left + "px";
  }
}

function drawFilters(){ paletteBar($("#palette")); axisBar($("#axes")); popover(); }

// Close an open dropdown on a click elsewhere. The origin is recorded during
// CAPTURE because redrawing detaches the very button that was clicked — by the
// bubble phase "was this inside?" would answer no, closing what just opened.
let clickInside = false;
document.addEventListener("click", e => {
  clickInside = $("#palette").contains(e.target) || $("#axes").contains(e.target) || $("#pop").contains(e.target);
}, true);
document.addEventListener("click", () => {
  if(OPEN_AXIS && !clickInside){ OPEN_AXIS = null; popover(); }
});
window.addEventListener("resize", () => {
  balanceWrap($("#axes")); popover();
});

function open(v){
  CURRENT = v;
  const name = v.name;
  $("#dlgName").textContent = name;
  $("#dlgDesc").textContent = v.description;
  if(EMBED) $("#dlgFrame").srcdoc = previewDoc(v.axes); else $("#dlgFrame").src = previewUrl(name);
  $("#dlgCopy").onclick = ()=>copy(name);

  const post = (path, body) => fetch(path, {
    method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify(body)
  }).then(r=>r.json()).catch(e=>({error:String(e)}));

  const act = async (button, label, busy, path, done) => {
    button.disabled = true; button.textContent = busy;
    const r = await post(path, { name });   // publish/export the recoloured spec
    button.disabled = false; button.textContent = label;
    toast(r.error ? (label + " failed: " + r.error) : done(r));
  };

  const ex = $("#dlgExport"), pub = $("#dlgPublish");
  ex.hidden = pub.hidden = !EXPORTABLE;
  if(EXPORTABLE){
    ex.onclick = ()=>act(ex, "Export PDF", "Exporting…", "/api/export",
                         r => "Exported " + r.path.split("/").pop());
    // The whole point of browsing: end on the deliverable, not on a name to
    // copy somewhere else.
    pub.onclick = ()=>act(pub, "★ Make this my resume", "Publishing…", "/api/publish",
                          r => "Published " + r.stem + ".pdf / .html / .md");
  }
  if(!$("#dlg").open){   // re-entrant when a swatch recolours an open dialog
    $("#dlg").showModal();
    document.body.classList.add("modal-open");
  }
}

// Filters travel with every page request — one param per selected value, so
// `?palette=moss&palette=plum` is an OR — and paging walks only the matching
// subset while the server reports its true size.
function filterQuery(){
  const p = new URLSearchParams();
  AXES.forEach(a => FILTERS[a.key].forEach(v => p.append(a.key, v)));
  const q = p.toString();
  return q ? "&" + q : "";
}

async function goto(index){
  if(EMBED){                       // no server: compute the page from the baked space
    const r = embedPage(index);
    OPTIONS = r.options; PAGE_INDEX = r.index; PAGES = r.pages; TOTAL = r.total; cursor = 0;
    OPEN_AXIS = null; render(); scrollTo({ top: 0, behavior: "smooth" });
    return;
  }
  const nav = $("#nav"); nav.style.opacity = ".5";
  const r = await fetch("/api/page?i=" + index + filterQuery()).then(r=>r.json())
                  .catch(e=>({error:String(e)}));
  nav.style.opacity = "1";
  if(r.error){ toast("Could not load page: " + r.error); return; }
  OPTIONS = r.options; PAGE_INDEX = r.index; PAGES = r.pages; TOTAL = r.total; cursor = 0;
  OPEN_AXIS = null;          // the dropdown's job is done once the browse has moved
  render();
  scrollTo({ top: 0, behavior: "smooth" });
}

if(PAGES > 1){
  $("#first").onclick   = ()=>goto(0);
  $("#next").onclick    = ()=>goto(PAGE_INDEX + 1);
  $("#prev").onclick    = ()=>goto(PAGE_INDEX - 1 + PAGES);
  // Somewhere else in the space entirely, rather than the next twelve along.
  $("#shuffle").onclick = ()=>goto(Math.floor(Math.random() * PAGES));
}

$("#dlgClose").onclick = ()=>$("#dlg").close();
$("#dlg").addEventListener("close", ()=>document.body.classList.remove("modal-open"));

addEventListener("keydown", e => {
  if($("#dlg").open){ if(e.key==="Escape") $("#dlg").close(); return; }
  if(e.key==="ArrowRight"||e.key==="j"){ cursor=Math.min(cursor+1,OPTIONS.length-1); }
  else if(e.key==="ArrowLeft"||e.key==="k"){ cursor=Math.max(cursor-1,0); }
  else if(e.key==="Enter"&&OPTIONS[cursor]){ open(OPTIONS[cursor]); }
  else if(PAGES>1&&(e.key==="]"||e.key==="n")){ goto(PAGE_INDEX+1); }
  else if(PAGES>1&&(e.key==="["||e.key==="p")){ goto(PAGE_INDEX-1+PAGES); }
});

if(EMBED){ buildSpace(); goto(0); } else { render(); }
</script>
</body></html>
"""
