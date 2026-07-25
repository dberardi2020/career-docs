"""Linter rules — each asserted by breaking exactly one thing.

The fixture is clean, so a rule firing means the mutation caused it. The most
important test in this file is the last one: the linter must *report* a missing
number and never be satisfiable by an invented one.
"""
from __future__ import annotations

from career_docs import compose, lint


def rules(resume, **kw) -> set[str]:
    return {f.rule for f in lint.check(resume, **kw)}


def level_of(resume, rule) -> str:
    return next(f.level for f in lint.check(resume) if f.rule == rule)


def test_a_clean_resume_raises_no_errors(resume):
    findings = lint.check(resume)
    assert [f for f in findings if f.level == lint.ERROR] == []


# ── contact ───────────────────────────────────────────────────────────────────

def test_missing_email_is_an_error(make_resume):
    r = make_resume(lambda d: d["basics"].pop("email"))
    assert "contact/email" in rules(r)
    assert level_of(r, "contact/email") == lint.ERROR


def test_missing_phone_warns(make_resume):
    r = make_resume(lambda d: d["basics"].pop("phone"))
    assert "contact/phone" in rules(r)


def test_street_address_warns(make_resume):
    r = make_resume(lambda d: d["basics"]["location"].update(address="123 Main Street"))
    assert "contact/street-address" in rules(r)


# ── summary ───────────────────────────────────────────────────────────────────

def test_objective_style_summary_is_an_error(make_resume):
    r = make_resume(lambda d: d["basics"].update(
        summary="Seeking a challenging role where I can grow my skills."))
    assert "summary/objective" in rules(r)
    assert level_of(r, "summary/objective") == lint.ERROR


def test_missing_summary_is_flagged(make_resume):
    r = make_resume(lambda d: d["basics"].pop("summary"))
    assert "summary/missing" in rules(r)


def test_unquantified_summary_is_flagged(make_resume):
    r = make_resume(lambda d: d["basics"].update(
        summary="Backend engineer who builds APIs and enjoys working on teams."))
    assert "summary/unquantified" in rules(r)


# ── experience ────────────────────────────────────────────────────────────────

def test_role_without_bullets_is_an_error(make_resume):
    r = make_resume(lambda d: d["work"][0].update(highlights=[]))
    assert "work/no-highlights" in rules(r)


def test_role_without_a_figure_is_flagged(make_resume):
    r = make_resume(lambda d: d["work"][0].update(
        highlights=["Built the billing API.", "Improved the deployment process."]))
    assert "work/unquantified" in rules(r)


def test_thin_recent_role_warns(make_resume):
    r = make_resume(lambda d: d["work"][0].update(
        highlights=["Shipped 14 API endpoints backing the billing product."]))
    assert "work/thin-role" in rules(r)


def test_vague_scope_is_flagged(make_resume):
    r = make_resume(lambda d: d["work"][0]["highlights"].append(
        "Responsible for various services and helped with multiple migrations."))
    assert "work/vague-scope" in rules(r)


def test_no_work_history_is_an_error(make_resume):
    r = make_resume(lambda d: d.update(work=[]))
    assert "work/missing" in rules(r)


# ── skills & obsolete ─────────────────────────────────────────────────────────

def test_missing_skills_warns(make_resume):
    r = make_resume(lambda d: d.update(skills=[]))
    assert "skills/missing" in rules(r)


def test_obsolete_phrase_warns(make_resume):
    r = make_resume(lambda d: d["basics"].update(
        summary=d["basics"]["summary"] + " References available upon request."))
    assert "obsolete/phrase" in rules(r)


# ── layout ────────────────────────────────────────────────────────────────────

def test_layout_rules_are_skipped_without_a_theme(resume):
    assert not any(r.startswith("layout/") for r in rules(resume, theme=None))


def test_generated_layouts_never_trip_a_layout_rule(resume):
    from career_docs import space
    for spec in space.spread(30):
        found = rules(resume, theme=compose.as_theme(spec))
        assert not any(r.startswith("layout/") for r in found), spec.name


def test_multi_column_layout_is_an_error(resume):
    unsafe = compose.Theme(name="two-col", description="", render=lambda r: "",
                           columns=2, min_font_pt=11.0, remote_assets=False,
                           ats_safe=False)
    assert "layout/multi-column" in rules(resume, theme=unsafe)


def test_small_type_warns(resume):
    tiny = compose.Theme(name="tiny", description="", render=lambda r: "",
                         columns=1, min_font_pt=8.0, remote_assets=False,
                         ats_safe=True)
    assert "layout/small-type" in rules(resume, theme=tiny)


def test_remote_assets_warn(resume):
    remote = compose.Theme(name="cdn", description="", render=lambda r: "",
                           columns=1, min_font_pt=11.0, remote_assets=True,
                           ats_safe=True)
    assert "layout/remote-assets" in rules(resume, theme=remote)


# ── the anti-fabrication contract ─────────────────────────────────────────────

def test_the_linter_only_ever_reports(make_resume):
    """It must never be able to *fix* a missing figure — only ask for one.

    This is the counterweight to the rule the workspace states in prose: a linter
    that demands metrics, pointed at a generative model, is a machine for
    manufacturing plausible lies about a career. Keeping `check` a pure reporter
    is what makes that rule enforceable rather than merely stated.
    """
    before = None

    def capture(d):
        nonlocal before
        d["work"][0]["highlights"] = ["Built the billing API."]
        before = [h for h in d["work"][0]["highlights"]]

    r = make_resume(capture)
    findings = lint.check(r)

    assert "work/unquantified" in {f.rule for f in findings}
    # The document is untouched: no number appeared anywhere.
    assert r.data["work"][0]["highlights"] == before


def test_the_unquantified_message_asks_rather_than_supplies(make_resume):
    r = make_resume(lambda d: d["work"][0].update(highlights=["Built the API."]))
    message = next(f.message for f in lint.check(r) if f.rule == "work/unquantified")
    assert "never invent" in message.lower()


def test_underscore_prefixed_keys_are_not_flagged(make_resume):
    """`_comment` / `$schema` are the universal "ignore me" convention.

    The demo profile carries a `_comment` marking it fictional; warning on it
    every publish would be noise, not help.
    """
    r = make_resume(lambda d: d.update(_comment="fictional", _note="x"))
    assert not any("Unknown top-level" in note for note in r.notes)


def test_a_genuine_unknown_section_is_still_flagged(make_resume):
    r = make_resume(lambda d: d.update(experiance="typo of experience"))
    assert any("Unknown top-level" in note and "experiance" in note for note in r.notes)
