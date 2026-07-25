"""PDF export, and the claim that matters about it.

A resume that renders beautifully and extracts as garbage is worse than useless,
because the failure is invisible to the person sending it. So this does not check
that a PDF was produced — it re-extracts the text and asserts the content survived
the round trip, which is exactly what a parser on the other end will do.

Skipped rather than failed where the machine cannot run it: PDF needs a
Chromium-family browser, and extraction needs PyMuPDF.
"""
from __future__ import annotations

import pytest

from career_docs import compose, model, pdf, space

fitz = pytest.importorskip("fitz", reason="PyMuPDF not installed")

try:
    pdf.find_browser()
except pdf.BrowserNotFound:
    pytest.skip("no Chromium-family browser available", allow_module_level=True)


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    import json

    from tests.conftest import CLEAN

    folder = tmp_path_factory.mktemp("pdf")
    source = folder / "resume.json"
    source.write_text(json.dumps(CLEAN), encoding="utf-8")
    resume = model.load(source)

    spec = compose.PRESETS["default"]
    out = folder / "resume.pdf"
    pdf.write(compose.render(resume, spec), out)
    return out


def _text(path) -> str:
    with fitz.open(path) as document:
        return "\n".join(page.get_text() for page in document)


def test_a_pdf_is_produced(rendered):
    assert rendered.exists()
    assert rendered.read_bytes().startswith(b"%PDF")


def test_the_pdf_is_one_page(rendered):
    with fitz.open(rendered) as document:
        assert document.page_count == 1


def test_the_identity_survives_extraction(rendered):
    text = _text(rendered)
    assert "Jane Smith" in text
    assert "jane@example.com" in text


def test_every_skill_survives_extraction(rendered):
    """Skills are what a keyword screen reads. None may be lost in the render."""
    text = _text(rendered)
    for keyword in ("Python", "Go", "SQL", "Docker", "Postgres"):
        assert keyword in text, keyword


def test_the_work_history_survives_extraction(rendered):
    text = _text(rendered)
    assert "Northwind" in text
    assert "Contoso" in text
    assert "billing" in text.lower()


def test_text_is_not_scrambled_by_the_layout(rendered):
    """Parsers read top-to-bottom, left-to-right.

    The mechanism claim behind every layout rule: single-column output must come
    back in document order. A two-column layout would interleave the roles.
    """
    text = _text(rendered)
    assert text.index("Northwind") < text.index("Contoso")
    assert text.index("Jane Smith") < text.index("Northwind")


@pytest.mark.parametrize("header", compose.HEADERS)
def test_no_layout_prints_to_the_paper_edge(tmp_path, header):
    """Every page of every layout keeps a real margin.

    The `band` header bleeds a dark banner to the paper edge, which needs a page
    box with no margin. Setting that globally cost *every* page its margins, so a
    resume running onto a second page put body text 1.6pt from the edge — outside
    the printable area of most printers. The bleed now applies only to the first
    page, where the banner is.

    A long profile is used deliberately: the bug was invisible on anything that
    fitted on one page.
    """
    import json

    from tests.conftest import CLEAN

    long_profile = json.loads(json.dumps(CLEAN))
    long_profile["work"] *= 4  # force a second page
    source = tmp_path / "resume.json"
    source.write_text(json.dumps(long_profile), encoding="utf-8")
    resume = model.load(source)

    spec = compose.Spec(0, 0, header, "pills", "ladder", 1)
    out = tmp_path / f"{spec.name}.pdf"
    pdf.write(compose.render(resume, spec), out)

    with fitz.open(out) as document:
        assert document.page_count > 1, "fixture no longer spans pages"
        for number, page in enumerate(document):
            blocks = page.get_text("blocks")
            if not blocks:
                continue
            left = min(b[0] for b in blocks)
            top = min(b[1] for b in blocks)
            assert left >= 25, f"{spec.name} page {number + 1}: left margin {left:.1f}pt"
            # Page 1 of a bleeding header is the banner itself, which is meant to
            # touch the top edge; its text is still inset by the banner's padding.
            assert top >= 25, f"{spec.name} page {number + 1}: top margin {top:.1f}pt"


@pytest.mark.parametrize("spec", space.spread(3), ids=lambda s: s.name)
def test_a_spread_of_layouts_all_extract_cleanly(tmp_path, spec):
    import json

    from tests.conftest import CLEAN

    source = tmp_path / "resume.json"
    source.write_text(json.dumps(CLEAN), encoding="utf-8")
    resume = model.load(source)

    out = tmp_path / f"{spec.name}.pdf"
    pdf.write(compose.render(resume, spec), out)
    # Case-insensitively: some headers set `text-transform: uppercase`, and a PDF
    # carries the transformed glyphs. A parser still reads the name either way.
    text = _text(out).lower()
    assert "jane smith" in text
    assert "northwind" in text
