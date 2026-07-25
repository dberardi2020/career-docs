"""Title history within one employer — the model, and the two ways it renders.

A promotion is evidence, and the evidence is *which bullets were earned at which
level*. The older `promotions` field held prior titles but no bullets, so a
resume could say "promoted" and never show what changed. `stints` fixes that, and
these tests pin the two things that could quietly break it: that legacy documents
still render, and that no bullet is ever dropped by either layout.
"""
from __future__ import annotations

import json

import pytest

from career_docs import compose, model

PROMOTED = {
    "name": "Northwind",
    "position": "Staff Engineer",
    "location": "Portland, OR",
    "startDate": "2021-03",
    "highlights": ["Company-level bullet spanning both titles."],
    "stints": [
        {"position": "Staff Engineer", "startDate": "2023-06",
         "highlights": ["Led the platform team of 6.", "Owned 3 services."]},
        {"position": "Senior Engineer", "startDate": "2021-03", "endDate": "2023-06",
         "highlights": ["Shipped 14 API endpoints."]},
    ],
}


def load(tmp_path, work) -> model.Resume:
    from tests.conftest import CLEAN
    payload = json.loads(json.dumps(CLEAN))
    payload["work"] = work
    path = tmp_path / "resume.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return model.load(path)


# ── the model ─────────────────────────────────────────────────────────────────

def test_a_role_without_progression_has_no_stints():
    assert model.stints({"position": "Engineer", "highlights": ["x"]}) == []


def test_stints_are_newest_first():
    got = [s["position"] for s in model.stints(PROMOTED)]
    assert got == ["Staff Engineer", "Senior Engineer"]


def test_legacy_promotions_normalise_into_stints():
    """Documents written before `stints` must keep rendering."""
    legacy = {
        "name": "Northwind", "position": "Staff Engineer",
        "startDate": "2021-03",
        "promotions": [{"title": "Senior Engineer",
                        "startDate": "2021-03", "endDate": "2023-06"}],
    }
    got = model.stints(legacy)
    assert [s.get("position") or s.get("title") for s in got] == [
        "Staff Engineer", "Senior Engineer"]
    # The current title starts where the prior one ended.
    assert got[0]["startDate"] == "2023-06"


def test_highlights_of_collects_every_bullet():
    got = model.highlights_of(PROMOTED)
    assert len(got) == 4
    assert "Company-level bullet spanning both titles." in got
    assert "Shipped 14 API endpoints." in got


@pytest.mark.parametrize("broken,message", [
    ({"stints": "nope"}, "must be an array"),
    ({"stints": [{"startDate": "2021-03"}]}, "position is required"),
    ({"stints": [{"position": "X", "startDate": "nope"}]}, "ISO 8601"),
    ({"stints": [{"position": "X", "startDate": "2023", "endDate": "2021"}]},
     "before it starts"),
    ({"stints": [{"position": "X", "highlights": "nope"}]}, "must be an array"),
])
def test_bad_stints_are_rejected(tmp_path, broken, message):
    with pytest.raises(model.ResumeError) as exc:
        load(tmp_path, [{"name": "N", "position": "P",
                         "highlights": ["1 thing"], **broken}])
    assert message in str(exc.value)


def test_stints_and_legacy_promotions_together_are_rejected(tmp_path):
    """Two sources of truth for the same fact is exactly the drift to prevent."""
    with pytest.raises(model.ResumeError) as exc:
        load(tmp_path, [{**PROMOTED,
                         "promotions": [{"title": "Senior Engineer"}]}])
    assert "supersedes" in str(exc.value)


# ── rendering ─────────────────────────────────────────────────────────────────

def spec(grouping, promo="ladder"):
    return compose.Spec(0, 0, "band", "pills", promo, 1, grouping)


@pytest.mark.parametrize("grouping", compose.GROUPINGS)
@pytest.mark.parametrize("promo", compose.PROMOS)
def test_no_bullet_is_ever_dropped(tmp_path, grouping, promo):
    """Whatever the layout, every bullet in the data reaches the page."""
    resume = load(tmp_path, [PROMOTED])
    html = compose.render(resume, spec(grouping, promo))
    for bullet in model.highlights_of(PROMOTED):
        assert bullet in html, (grouping, promo, bullet)


@pytest.mark.parametrize("grouping", compose.GROUPINGS)
def test_every_title_is_named(tmp_path, grouping):
    resume = load(tmp_path, [PROMOTED])
    html = compose.render(resume, spec(grouping))
    assert "Staff Engineer" in html
    assert "Senior Engineer" in html


def test_the_two_groupings_are_genuinely_different(tmp_path):
    resume = load(tmp_path, [PROMOTED])
    assert compose.render(resume, spec("grouped")) != \
           compose.render(resume, spec("flat"))


def test_grouped_names_the_employer_once(tmp_path):
    """Employer as heading, titles nested — the employer should not repeat."""
    resume = load(tmp_path, [PROMOTED])
    html = compose.render(resume, spec("grouped"))
    assert html.count(">Northwind<") == 1


def test_flat_repeats_the_employer_per_title(tmp_path):
    resume = load(tmp_path, [PROMOTED])
    html = compose.render(resume, spec("flat"))
    assert html.count("Northwind") >= 2


def test_grouping_is_invisible_without_a_promotion(tmp_path, data):
    """Most roles have no progression; the axis must not invent a difference."""
    resume = load(tmp_path, data["work"])
    assert compose.render(resume, spec("grouped")) == \
           compose.render(resume, spec("flat"))


def test_the_current_title_is_not_printed_twice(tmp_path):
    resume = load(tmp_path, [PROMOTED])
    html = compose.render(resume, spec("grouped"))
    assert html.count("Staff Engineer") == 1
