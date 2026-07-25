"""Rendering: the safety claims, escaping, and that the whole space renders.

The claims the linter trusts — single column, >=10pt, no remote assets — are
"by construction" claims. That only stays true if something checks the whole
space, so this walks every layout in it rather than a sample.
"""
from __future__ import annotations

import re

import pytest

from career_docs import compose, space

ALL = compose.all_specs()


def test_every_layout_renders(resume):
    """Not one spec in the space may raise. This is the load-bearing test."""
    for spec in ALL:
        html = compose.render(resume, spec)
        assert html.startswith("<!doctype html>")
        assert "</html>" in html


def test_every_layout_is_declared_ats_safe():
    for spec in ALL:
        theme = compose.as_theme(spec)
        assert theme.columns == 1
        assert theme.min_font_pt >= 10.0
        assert theme.remote_assets is False
        assert theme.ats_safe is True


def test_no_layout_reaches_the_network(resume):
    """`remote_assets = False` is a promise; a stray CDN font would break it."""
    for spec in space.spread(60):
        html = compose.render(resume, spec)
        assert "http://" not in html
        assert not re.search(r'src\s*=\s*"https?://', html)
        assert "@import" not in html


def test_every_layout_is_inset_on_screen(resume):
    """`@page` margins are print-only; a preview needs its own inset.

    Without this, every non-bleeding layout rendered text hard against the edge
    of the viewport — correct on paper, wrong in every preview, and previews are
    what people judge a layout by.
    """
    for spec in space.spread(40):
        css = compose.css(spec)
        assert "@media screen" in css, spec.name
        screen = css.split("@media screen", 1)[1]
        if spec.header == "band":
            # Bleeds by design; the inset comes from `.wrap` instead.
            assert "padding:0.3in" in css, spec.name
        else:
            assert "padding: 0.55in" in screen, spec.name


def test_no_layout_uses_multiple_columns(resume):
    """The parse-safety claim, checked against the CSS that makes it.

    Only the CSS *multi-column* properties flow text into parallel columns, which
    is what scrambles a parser's reading order. `grid-template-columns` does not —
    it lays out discrete items (the skills grid), each still read in document
    order — so it must not trip this.
    """
    multicol = re.compile(r"(?<![-\w])(columns|column-count|column-width)\s*:")
    for spec in space.spread(60):
        css = compose.css(spec)
        assert not multicol.search(css), spec.name


def test_the_content_survives_rendering(resume):
    html = compose.render(resume, ALL[0])
    assert "Jane Smith" in html
    assert "Northwind" in html
    assert "Shipped 14 API endpoints backing the billing product." in html
    for keyword in ("Python", "Go", "SQL", "Docker", "Postgres"):
        assert keyword in html


def test_every_skill_renders_in_every_skills_treatment(resume):
    """Curation is a rendering choice, but nothing may be silently dropped."""
    for treatment in compose.SKILLS:
        spec = compose.Spec(0, 0, "band", treatment, "ladder", 1)
        html = compose.render(resume, spec)
        for keyword in ("Python", "Go", "SQL", "Docker", "Postgres"):
            assert keyword in html, (treatment, keyword)


def test_content_is_html_escaped(make_resume):
    hostile = make_resume(
        lambda d: d["work"][0]["highlights"].insert(0, '<script>alert("x")</script> & more'))
    html = compose.render(hostile, ALL[0])
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html
    assert "&amp; more" in html


def test_render_is_pure(resume):
    """Same inputs, same bytes — what makes previews and publishes agree."""
    spec = ALL[100]
    assert compose.render(resume, spec) == compose.render(resume, spec)


def test_different_specs_render_differently(resume):
    a = compose.render(resume, compose.Spec(0, 0, "band", "pills", "ladder", 0))
    b = compose.render(resume, compose.Spec(1, 0, "band", "pills", "ladder", 0))
    assert a != b


def test_presets_are_specs_in_the_space():
    for name, spec in compose.PRESETS.items():
        assert compose.preset(name) == spec
        assert space.parse(spec.name) == spec, name


def test_preset_of_an_unknown_name_is_none():
    assert compose.preset("no-such-preset") is None


def test_as_theme_carries_the_spec_name():
    spec = ALL[0]
    assert compose.as_theme(spec).name == spec.name


@pytest.mark.parametrize("value,expected", [
    ("<b>", "&lt;b&gt;"),
    ("a & b", "a &amp; b"),
    (None, ""),
    ('"quoted"', "&quot;quoted&quot;"),
])
def test_esc(value, expected):
    assert compose.esc(value) == expected
