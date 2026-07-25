"""The hosted static demo — the delivery that had no tests at all.

`demo.py` shipped the whole RP-0038 slice (bake, the embed viewer, the landing page)
with nothing covering it: no unit test imported the module, and no acceptance check
built it. It is also the only surface that goes on the public internet. These are the
build-level guarantees — that the site is emitted, self-contained, and that its
browser is the same delivery the local catalogue runs.
"""
from __future__ import annotations

import json

from career_docs import catalogue, demo, space, viewer


def test_the_build_emits_a_self_contained_site(resume, tmp_path):
    index = demo.build(resume, tmp_path, count=6)
    assert index.name == "index.html"
    browse = tmp_path / "browse.html"
    assert browse.is_file()
    # Every hero layout is written beside the landing for its carousel to point at.
    for spec in demo.HERO_SPECS:
        assert (tmp_path / f"{spec.name}.html").is_file()


def test_the_site_reaches_for_nothing_off_the_box(resume, tmp_path):
    """No CDN, no remote fonts, no analytics — a shared link has to work instantly
    and offline, and the renderer's whole ethos is no dependencies."""
    demo.build(resume, tmp_path, count=6)
    for page in ("index.html", "browse.html"):
        text = (tmp_path / page).read_text()
        assert "https://fonts." not in text
        assert "cdn." not in text
        assert "<script src=" not in text


def test_a_rebuilt_site_drops_pages_from_the_previous_run(resume, tmp_path):
    """A hero set can change; a stale layout left behind would be served forever."""
    stale = tmp_path / "not-a-real-spec.html"
    tmp_path.mkdir(parents=True, exist_ok=True)
    stale.write_text("<html>old</html>")
    demo.build(resume, tmp_path, count=6)
    assert not stale.exists()


def test_the_landing_links_to_the_browser(resume, tmp_path):
    demo.build(resume, tmp_path, count=6)
    landing = (tmp_path / "index.html").read_text()
    assert "./browse.html" in landing
    assert f"{space.TOTAL:,}" in landing


def test_both_static_outputs_run_the_same_delivery(resume, tmp_path):
    """The hosted demo and the local catalogue are one delivery (ADR-0004). If they
    diverge, the thing you check locally stops predicting what you ship."""
    demo.build(resume, tmp_path / "site", count=6)
    catalogue.build(resume, 6, tmp_path / "cat", source=tmp_path / "resume.json")
    hosted = (tmp_path / "site" / "browse.html").read_text()
    local = (tmp_path / "cat" / "index.html").read_text()
    for page in (hosted, local):
        assert 'const PREVIEW    = "embed"' in page
        assert "const MARKUPS = null" not in page


def test_the_catalogue_still_writes_its_own_artifacts(resume, tmp_path):
    """Switching the index to embed must not cost the per-layout files or
    options.json — that is the part you commit, link, or hand to an agent."""
    index, specs = catalogue.build(resume, 6, tmp_path, source=tmp_path / "resume.json")
    for spec in specs:
        assert (tmp_path / f"{spec.name}.html").is_file()
    options = json.loads((tmp_path / "options.json").read_text())["options"]
    assert [o["name"] for o in options] == [s.name for s in specs]
    assert all(o["preview"] == f"{o['name']}.html" for o in options)
