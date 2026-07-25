"""The viewer — one page, two deliveries.

These tests exist because there used to be two implementations of this page. The
point is that the *only* differences between the served and static deliveries are
where previews come from and whether export is offered.
"""
from __future__ import annotations

import json
import re

import pytest

from resume_pipeline import compose, space, viewer

SPECS = space.spread(5)


def _options(html: str) -> list[dict]:
    match = re.search(r"^let\s+OPTIONS\s*=\s*(\[.*\]);$", html, re.MULTILINE)
    assert match, "OPTIONS payload not found in page"
    return json.loads(match.group(1))


def test_page_embeds_every_spec(resume):
    options = _options(viewer.page(SPECS, resume))
    assert [o["name"] for o in options] == [s.name for s in SPECS]


def test_page_embeds_the_axes_as_facets(resume):
    options = _options(viewer.page(SPECS, resume))
    assert all(set(o["axes"]) == {"palette", "typeface", "header", "skills",
                                  "promo", "density", "grouping"}
               for o in options)


def _embed(resume, **kw):
    """The static delivery, with the tables it runs on."""
    data = viewer.bake(resume)
    return viewer.page(SPECS, resume, preview="embed", markups=data["markups"],
                       css=data["css"], **kw), data


def test_static_delivery_rebuilds_previews_in_the_browser(resume):
    html, _ = _embed(resume)
    assert 'const PREVIEW    = "embed"' in html
    assert 'const EXPORTABLE = false' in html
    assert "const MARKUPS = null" not in html      # the tables actually shipped


def test_served_delivery_points_at_the_preview_route(resume):
    html = viewer.page(SPECS, resume, preview="route", exportable=True)
    assert 'const PREVIEW    = "route"' in html
    assert 'const EXPORTABLE = true' in html


def test_there_is_no_third_delivery(resume):
    """`preview="file"` was a lesser static mode — a fixed sample with no filters,
    and the one place a bug could hide from every other delivery. It is gone, and an
    unknown delivery is an error rather than a page that half works (ADR-0004)."""
    with pytest.raises(ValueError, match="unknown delivery"):
        viewer.page(SPECS, resume, preview="file")


def test_the_static_delivery_cannot_ship_without_its_tables(resume):
    """embed rebuilds every preview from the baked tables; without them the page
    would render an empty grid instead of failing the build."""
    with pytest.raises(ValueError, match="baked markups/css"):
        viewer.page(SPECS, resume, preview="embed")


def test_the_two_deliveries_differ_only_in_those_switches(resume):
    """ADR-0004's guardrail: normalise the delivery switches and the two pages are
    byte-equal, so a third difference cannot appear without someone deciding to add
    it. This is the test that did *not* cover embed when embed was added."""
    embed, data = _embed(resume)
    served = viewer.page(SPECS, resume, preview="route", exportable=True)

    def normalise(h):
        # The baked tables are the payload embed runs on, not a difference in the
        # page; blank them and the two must agree line for line.
        h = re.sub(r"^const (MARKUPS|CSSTAB)  ?= .*$", r"const \1 =", h, flags=re.M)
        return (h.replace('"embed"', '"route"')
                 .replace("EXPORTABLE = true", "EXPORTABLE = false"))

    assert normalise(served) == normalise(embed)


def test_the_resume_name_titles_the_page(resume):
    assert "Jane Smith — Layouts" in viewer.page(SPECS, resume)


def test_a_hostile_name_cannot_break_out_of_the_title(make_resume):
    hostile = make_resume(lambda d: d["basics"].update(name="</title><script>x</script>"))
    html = viewer.page(SPECS, hostile)
    assert "</title><script>" not in html
    assert "&lt;/title&gt;" in html


def test_describe_matches_the_spec():
    spec = SPECS[0]
    described = viewer.describe(spec)
    assert described["name"] == spec.name
    assert described["description"] == spec.description
    assert described["axes"]["palette"] == compose.PALETTES[spec.palette][0]


def test_page_is_self_contained(resume):
    """It must work from `file://` — no external stylesheet, script, or font."""
    html = viewer.page(SPECS, resume)
    assert "http://" not in html
    assert not re.search(r'<(script|link)[^>]+(src|href)\s*=\s*"https?://', html)


# ── the colour bar ────────────────────────────────────────────────────────────

def test_the_served_viewer_offers_every_palette(resume):
    html = viewer.page(SPECS, resume, preview="route", exportable=True, pages=10)
    import re
    pals = json.loads(re.search(r"const PALETTES\s*=\s*(\[.*?\]);", html).group(1))
    assert [p["name"] for p in pals] == [p[0] for p in compose.PALETTES]
    # Both deliveries filter now — the static one client-side — so there is no
    # longer a mode where these controls are absent.
    assert "const FILTERS    = Object.fromEntries" in html


def test_the_served_viewer_offers_every_typeface(resume):
    """Every face, each carrying its own font stack so a sample renders in it."""
    html = viewer.page(SPECS, resume, preview="route", exportable=True, pages=10)
    tfs = json.loads(re.search(r"const TYPEFACES\s*=\s*(\[.*?\]);", html).group(1))
    assert [t["name"] for t in tfs] == [t[0] for t in compose.TYPEFACES]
    assert all(t["font"] == compose.TYPEFACES[i][1] for i, t in enumerate(tfs))


def test_a_typeface_swap_changes_that_axis_only():
    """Typeface is the *second* name segment, so a name with that segment swapped is
    the same layout in another face — the invariant `parse` and the filters rely on."""
    spec = compose.Spec(0, 0, "band", "pills", "ladder", 1, "grouped")
    assert spec.name.split("-")[1] == "grotesk"
    parts = spec.name.split("-")
    parts[1] = "charter"
    other = space.parse("-".join(parts))
    assert other is not None
    assert compose.TYPEFACES[other.typeface][0] == "charter"
    # every axis but typeface is identical
    assert (other.palette, other.header, other.skills,
            other.promo, other.density, other.grouping) == \
           (spec.palette, spec.header, spec.skills,
            spec.promo, spec.density, spec.grouping)


def test_a_palette_swap_changes_that_axis_only():
    """Palette is the first name segment.

    So "this layout, that colour" is a different but equally valid spec, and the
    rest of the layout is untouched — which is why it can be an instant re-render
    rather than a live edit.
    """
    spec = compose.Spec(0, 0, "band", "pills", "ladder", 1, "grouped")
    assert spec.name.split("-")[0] == "harbor"
    recoloured = "moss" + spec.name[len("harbor"):]
    other = space.parse(recoloured)
    assert other is not None
    assert compose.PALETTES[other.palette][0] == "moss"
    # every axis but palette is identical
    assert (other.typeface, other.header, other.skills,
            other.promo, other.density, other.grouping) == \
           (spec.typeface, spec.header, spec.skills,
            spec.promo, spec.density, spec.grouping)


def test_the_first_page_button_exists_only_when_paging(resume):
    served = viewer.page(SPECS, resume, preview="route", exportable=True, pages=10)
    assert 'id="first"' in served


# ── multi-select filtering (RP-0033) ──────────────────────────────────────────

def test_the_viewer_ships_every_axis_with_its_values(resume):
    """One structure drives the dropdowns, the card chips and the query string, so
    they cannot disagree about what an axis is called or which values it has."""
    html = viewer.page(SPECS, resume, preview="route", exportable=True, pages=10)
    axes = json.loads(re.search(r"const AXES\s*=\s*(\[.*?\]);", html).group(1))
    assert [a["key"] for a in axes] == [k for k, _ in space.AXES]
    for a in axes:
        assert a["values"] == space.axis_values(a["key"])
    # `mixed` differs from `charter` only in its *body* face, so a sample has to
    # show display and body separately or the two look identical. Compare the
    # leading family: the fallback tails differ without meaning anything.
    fonts = next(a for a in axes if a["key"] == "typeface")["fonts"]
    lead = lambda stack: stack.split(",")[0].strip().strip('"')
    assert lead(fonts["charter"]["body"]) == lead(fonts["charter"]["display"])
    assert lead(fonts["mixed"]["body"]) != lead(fonts["mixed"]["display"])


def test_axis_values_cover_the_whole_space():
    product = 1
    for axis, _ in space.AXES:
        product *= len(space.axis_values(axis))
    assert product == space.TOTAL


def test_a_filter_may_hold_several_values_for_one_axis():
    """OR within an axis, AND across them — so two colours is twice one colour, and
    adding a typeface divides again."""
    one = space.total({"palette": ["moss"]})
    two = space.total({"palette": ["moss", "plum"]})
    assert one == space.TOTAL // len(compose.PALETTES)
    assert two == 2 * one
    both = space.total({"palette": ["moss", "plum"], "typeface": ["charter"]})
    assert both == two // len(compose.TYPEFACES)


def test_a_single_value_filter_matches_the_scalar_form():
    """A one-value list and the old scalar mean the same query, so nothing that
    passed a bare string has changed meaning."""
    assert space.total({"palette": "moss"}) == space.total({"palette": ["moss"]})
    page_scalar = [s.name for s in space.page(0, 6, {"palette": "moss"})]
    page_list = [s.name for s in space.page(0, 6, {"palette": ["moss"]})]
    assert page_scalar == page_list


def test_an_emptied_axis_means_unconstrained_not_impossible():
    """The viewer clears an axis by emptying its set rather than deleting the key.
    Reading that as 'matches nothing' would make Clear look like 'no results'."""
    assert space.total({"palette": []}) == space.TOTAL
    assert space.total({"palette": set()}) == space.TOTAL
    assert space.total({"palette": [], "typeface": ["charter"]}) == \
           space.total({"typeface": ["charter"]})


def test_selecting_every_value_of_an_axis_is_no_filter_at_all():
    """The degenerate case that made `grouping` look like it needed special
    handling: ticking every box is the same as ticking none — on every axis."""
    for axis, _ in space.AXES:
        assert space.total({axis: space.axis_values(axis)}) == space.TOTAL


def test_a_filtered_page_only_contains_matching_layouts():
    filters = {"palette": ["moss", "plum"], "density": ["compact"]}
    got = space.page(0, 24, filters)
    assert got
    for spec in got:
        assert compose.PALETTES[spec.palette][0] in {"moss", "plum"}
        assert compose.DENSITIES[spec.density][0] == "compact"


# ── the bake invariant ─────────────────────────────────────────────────────────
# This is the load-bearing claim of the static delivery: a rendered layout separates
# into a <body> that depends on four axes (120 combinations) and a <style> that
# depends on four others (168), so 288 renders can rebuild all 10,080 previews in a
# browser with no backend. If it ever stops holding, the hosted demo and the local
# catalogue start showing layouts that differ from what publishes — silently.
#
# It went untested from the day it shipped. The whole space costs ~0.3s to verify,
# so this checks every spec rather than a sample.

def test_baking_reassembles_every_layout_exactly(resume):
    data = viewer.bake(resume)
    specs = space.browse_order()
    assert len(specs) == space.TOTAL
    mismatched = [s.name for s in specs
                  if viewer.rebuild(s, data) != compose.render(resume, s).rstrip("\n")]
    assert not mismatched, f"{len(mismatched)} of {len(specs)} differ, e.g. {mismatched[:3]}"


def test_the_tables_are_small_because_the_axes_split(resume):
    """288 renders, not 10,080 — the separation is the point, so assert the sizes
    rather than trusting the comment."""
    data = viewer.bake(resume)
    assert len(data["markups"]) == 120
    assert len(data["css"]) == 168


def test_the_js_and_python_agree_on_the_table_keys(resume):
    """`previewDoc()` builds its keys in JS; `markup_key`/`css_key` build them here.
    They are separate implementations of one format, so pin the format."""
    spec = space.spread(1)[0]
    assert viewer.markup_key(spec) == "|".join(
        (spec.header, spec.skills, spec.promo, spec.grouping))
    assert viewer.css_key(spec) == "|".join(
        (str(spec.palette), str(spec.typeface), str(spec.density),
         "1" if spec.header == "band" else "0"))


def test_the_preview_title_matches_the_real_render(resume):
    """The page's own <title> falls back to "Resume" for a nameless profile; the
    preview's must not, or an embed preview would differ from what publishes."""
    data = viewer.bake(resume)
    html_ = viewer.page(SPECS, resume, preview="embed",
                        markups=data["markups"], css=data["css"])
    assert f'const DEMO_TITLE = {json.dumps(compose.esc(resume.name))}' in html_


# ── the local top bar ──────────────────────────────────────────────────────────

def test_the_local_bar_names_the_workspace_not_the_file(tmp_path):
    """`resume.json` is the filename in every workspace, so it identifies nothing.
    The workspace folder does — stepping up past the scaffold's generic `Resume/`."""
    from resume_pipeline import theme
    hq = tmp_path / "Career HQ" / "Resume"
    hq.mkdir(parents=True)
    (hq / "resume.json").touch()
    assert theme.workspace_label(hq / "resume.json") == "Career HQ"

    flat = tmp_path / "side-project"
    flat.mkdir()
    (flat / "resume.json").touch()
    assert theme.workspace_label(flat / "resume.json") == "side-project"


def test_the_local_bar_does_not_link_the_brand(tmp_path):
    """There is no landing page on your machine — `serve` mounts the viewer at `/`
    and nothing else — so a linked brand would point at the page you are on."""
    from resume_pipeline import theme
    bar = theme.local_nav(tmp_path / "Career HQ" / "Resume" / "resume.json")
    assert '<span class="brand">' in bar
    assert 'class="brand" href' not in bar
    assert "Overview" not in bar
