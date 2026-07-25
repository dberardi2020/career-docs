"""The command surface: locating the resume, resolving layouts, publishing."""
from __future__ import annotations

import json

import pytest

from career_docs import cli, compose

COMMANDS = {"lint", "catalogue", "demo", "serve", "publish", "init"}


def test_the_command_surface_is_exactly_this(monkeypatch):
    """A guard on scope. Growing this set should be a decision, not a drift."""
    import argparse
    parser = cli.build_parser()
    action = next(a for a in parser._actions
                  if isinstance(a, argparse._SubParsersAction))
    assert set(action.choices) == COMMANDS


# ── find_resume ───────────────────────────────────────────────────────────────

def test_explicit_path_wins(tmp_path, monkeypatch):
    target = tmp_path / "elsewhere.json"
    target.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("CAREER_DOCS_RESUME", str(tmp_path / "env.json"))
    assert cli.find_resume(str(target)) == target


def test_environment_variable_is_used(tmp_path, monkeypatch):
    target = tmp_path / "env.json"
    target.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("CAREER_DOCS_RESUME", str(target))
    assert cli.find_resume(None) == target


def test_it_walks_up_to_find_the_resume(tmp_path, monkeypatch):
    monkeypatch.delenv("CAREER_DOCS_RESUME", raising=False)
    (tmp_path / "Resume").mkdir()
    target = tmp_path / "Resume" / "resume.json"
    target.write_text("{}", encoding="utf-8")

    deep = tmp_path / "Resume" / "Archive" / "deep"
    deep.mkdir(parents=True)
    monkeypatch.chdir(deep)
    assert cli.find_resume(None) == target


def test_no_resume_anywhere_exits(tmp_path, monkeypatch):
    monkeypatch.delenv("CAREER_DOCS_RESUME", raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        cli.find_resume(None)


# ── resolve_layout ────────────────────────────────────────────────────────────

def test_presets_resolve():
    for name in compose.PRESETS:
        assert cli.resolve_layout(name).name


def test_generated_ids_resolve():
    """The generated half of the space must be publishable, not just viewable."""
    theme = cli.resolve_layout("moss-charter-rule-grid-stacked-compact-flat")
    assert theme.name == "moss-charter-rule-grid-stacked-compact-flat"


def test_an_unknown_layout_exits_with_help():
    with pytest.raises(SystemExit) as exc:
        cli.resolve_layout("harbor-321-mixed-compact")
    assert "unknown layout" in str(exc.value)
    assert "catalogue" in str(exc.value)


# ── cache_dir ─────────────────────────────────────────────────────────────────

def test_scratch_renders_stay_out_of_the_resume_folder(tmp_path):
    cache = cli.cache_dir(tmp_path / "Resume" / "resume.json")
    assert "career-docs" in cache.parts
    assert tmp_path not in cache.parents


# ── publish ───────────────────────────────────────────────────────────────────

@pytest.fixture
def workspace(tmp_path, data):
    folder = tmp_path / "Resume"
    folder.mkdir()
    (folder / "resume.json").write_text(json.dumps(data), encoding="utf-8")
    return folder


def test_publish_writes_the_deliverable(workspace, monkeypatch):
    monkeypatch.setattr("career_docs.pdf.write",
                        lambda html, path, **kw: path.write_bytes(b"%PDF-fake"))
    exit_code = cli.main(["publish", str(workspace / "resume.json"),
                          "--theme", "default", "--name", "Out"])
    assert exit_code == 0
    for suffix in (".html", ".md", ".pdf"):
        assert (workspace / f"Out{suffix}").exists()


def test_publish_overwrites_rather_than_accumulating(workspace, monkeypatch):
    monkeypatch.setattr("career_docs.pdf.write",
                        lambda html, path, **kw: path.write_bytes(b"%PDF-fake"))
    for theme in ("default", "plain"):
        cli.main(["publish", str(workspace / "resume.json"),
                  "--theme", theme, "--name", "Out"])
    assert len(list(workspace.glob("Out*"))) == 3


def test_publish_reports_a_pdf_failure(workspace, monkeypatch):
    def boom(html, path, **kw):
        raise RuntimeError("no browser here")
    monkeypatch.setattr("career_docs.pdf.write", boom)
    assert cli.main(["publish", str(workspace / "resume.json"),
                     "--theme", "default"]) == 1


# ── keeping the layout across a content edit ──────────────────────────────────

def _fake_pdf(monkeypatch):
    monkeypatch.setattr("career_docs.pdf.write",
                        lambda html, path, **kw: path.write_bytes(b"%PDF-fake"))


def test_publish_records_the_chosen_layout(workspace, monkeypatch):
    """The sidecar must remember which layout produced the deliverable."""
    from career_docs import compose, deliverable
    _fake_pdf(monkeypatch)
    cli.main(["publish", str(workspace / "resume.json"),
              "--theme", "plain", "--name", "Out"])
    assert (workspace / deliverable.SIDECAR).is_file()
    assert deliverable.recorded_layout(workspace) == compose.preset("plain").name


def test_bare_publish_keeps_the_last_layout(workspace, monkeypatch, capsys):
    """A content edit re-published without --theme keeps the chosen layout,
    rather than silently snapping back to the default."""
    from career_docs import compose, deliverable
    _fake_pdf(monkeypatch)
    plain = compose.preset("plain").name
    assert plain != compose.preset("default").name  # otherwise the test proves nothing
    cli.main(["publish", str(workspace / "resume.json"),
              "--theme", "plain", "--name", "Out"])
    capsys.readouterr()

    cli.main(["publish", str(workspace / "resume.json"), "--name", "Out"])
    assert deliverable.recorded_layout(workspace) == plain
    assert "kept your last layout" in capsys.readouterr().out


def test_the_layout_survives_deleting_every_deliverable(workspace, monkeypatch):
    """The whole point of the sidecar: the choice outlives the generated files."""
    from career_docs import compose, deliverable
    _fake_pdf(monkeypatch)
    cli.main(["publish", str(workspace / "resume.json"),
              "--theme", "plain", "--name", "Out"])
    for f in workspace.glob("Out.*"):
        f.unlink()
    assert deliverable.recorded_layout(workspace) == compose.preset("plain").name


def test_bare_publish_defaults_when_nothing_is_recorded(workspace, monkeypatch, capsys):
    from career_docs import compose, deliverable
    _fake_pdf(monkeypatch)
    cli.main(["publish", str(workspace / "resume.json"), "--name", "Out"])
    assert deliverable.recorded_layout(workspace) == compose.preset("default").name
    assert "kept your last layout" not in capsys.readouterr().out


def test_explicit_theme_overrides_the_recorded_layout(workspace, monkeypatch):
    from career_docs import compose, deliverable
    _fake_pdf(monkeypatch)
    cli.main(["publish", str(workspace / "resume.json"),
              "--theme", "plain", "--name", "Out"])
    cli.main(["publish", str(workspace / "resume.json"),
              "--theme", "default", "--name", "Out"])
    assert deliverable.recorded_layout(workspace) == compose.preset("default").name


def test_recorded_layout_is_none_without_a_sidecar(tmp_path):
    """A deliverable from before this feature has no sidecar — fall back."""
    from career_docs import deliverable
    for suffix in (".pdf", ".html", ".md"):
        (tmp_path / f"Out{suffix}").write_text("legacy", encoding="utf-8")
    assert deliverable.recorded_layout(tmp_path) is None


# ── choosing which formats to emit ────────────────────────────────────────────

def test_publish_writes_only_the_selected_formats(workspace, monkeypatch):
    from career_docs import deliverable
    _fake_pdf(monkeypatch)
    cli.main(["publish", str(workspace / "resume.json"),
              "--formats", "pdf", "--name", "Out"])
    assert (workspace / "Out.pdf").exists()
    assert not (workspace / "Out.html").exists()
    assert not (workspace / "Out.md").exists()
    assert deliverable.recorded_formats(workspace) == ["pdf"]


def test_bare_publish_keeps_the_last_formats(workspace, monkeypatch, capsys):
    _fake_pdf(monkeypatch)
    cli.main(["publish", str(workspace / "resume.json"),
              "--formats", "pdf", "--name", "Out"])
    capsys.readouterr()
    cli.main(["publish", str(workspace / "resume.json"), "--name", "Out"])
    assert not (workspace / "Out.html").exists()
    assert "kept your last" in capsys.readouterr().out


def test_a_pdf_only_deliverable_still_matches_its_name(workspace, monkeypatch):
    """Name reuse must survive a subset: a lone PDF is a complete deliverable
    when the sidecar records pdf-only."""
    from career_docs import deliverable
    _fake_pdf(monkeypatch)
    cli.main(["publish", str(workspace / "resume.json"),
              "--formats", "pdf", "--name", "OnlyPdf"])
    assert deliverable.existing_stem(workspace) == "OnlyPdf"


def test_an_unknown_format_is_rejected(workspace, monkeypatch):
    _fake_pdf(monkeypatch)
    with pytest.raises(SystemExit):
        cli.main(["publish", str(workspace / "resume.json"), "--formats", "docx"])


# ── archiving the previous design ─────────────────────────────────────────────

def test_publish_archives_the_previous_design(workspace, monkeypatch):
    from career_docs import deliverable
    _fake_pdf(monkeypatch)
    cli.main(["publish", str(workspace / "resume.json"), "--theme", "plain", "--name", "Out"])
    cli.main(["publish", str(workspace / "resume.json"), "--theme", "default", "--name", "Out"])
    snaps = list((workspace / deliverable.ARCHIVE_DIR).iterdir())
    assert len(snaps) == 1
    assert (snaps[0] / "Out.html").is_file() and (snaps[0] / "Out.pdf").is_file()


def test_first_publish_has_nothing_to_archive(workspace, monkeypatch):
    from career_docs import deliverable
    _fake_pdf(monkeypatch)
    cli.main(["publish", str(workspace / "resume.json"), "--name", "Out"])
    archive = workspace / deliverable.ARCHIVE_DIR
    assert not archive.exists() or not any(archive.iterdir())


def test_the_archived_copy_is_the_old_design_not_the_new(workspace, monkeypatch):
    from career_docs import deliverable
    _fake_pdf(monkeypatch)
    cli.main(["publish", str(workspace / "resume.json"), "--theme", "plain", "--name", "Out"])
    old_html = (workspace / "Out.html").read_text()
    cli.main(["publish", str(workspace / "resume.json"), "--theme", "editorial", "--name", "Out"])
    snap = next((workspace / deliverable.ARCHIVE_DIR).iterdir())
    assert (snap / "Out.html").read_text() == old_html
    assert (workspace / "Out.html").read_text() != old_html


def test_rapid_publishes_do_not_collide_in_the_archive(workspace, monkeypatch):
    """Two publishes in the same second must produce two distinct snapshots, not
    one clobbering the other — the guarantee is *never lose a design*."""
    from career_docs import deliverable
    _fake_pdf(monkeypatch)
    for theme in ("plain", "editorial", "default"):  # three publishes, back to back
        cli.main(["publish", str(workspace / "resume.json"), "--theme", theme, "--name", "Out"])
    snaps = list((workspace / deliverable.ARCHIVE_DIR).iterdir())
    assert len(snaps) == 2, [p.name for p in snaps]  # 1st archives nothing; 2nd and 3rd each once


def test_publish_never_touches_existing_archive_contents(workspace, monkeypatch):
    """The user's Archive is preserved: publishing only ever adds folders."""
    from career_docs import deliverable
    _fake_pdf(monkeypatch)
    keepsake = workspace / deliverable.ARCHIVE_DIR / "20200101-precious.json"
    keepsake.parent.mkdir(parents=True)
    keepsake.write_text("do not touch", encoding="utf-8")
    cli.main(["publish", str(workspace / "resume.json"), "--name", "Out"])
    cli.main(["publish", str(workspace / "resume.json"), "--name", "Out"])
    assert keepsake.read_text() == "do not touch"


def test_lint_exit_code_reflects_errors(workspace, capsys):
    assert cli.main(["lint", str(workspace / "resume.json")]) == 0

    broken = json.loads((workspace / "resume.json").read_text())
    broken["basics"].pop("email")
    (workspace / "resume.json").write_text(json.dumps(broken), encoding="utf-8")
    assert cli.main(["lint", str(workspace / "resume.json")]) == 1


def test_strict_lint_fails_on_warnings(workspace):
    payload = json.loads((workspace / "resume.json").read_text())
    payload["basics"].pop("phone")
    (workspace / "resume.json").write_text(json.dumps(payload), encoding="utf-8")

    assert cli.main(["lint", str(workspace / "resume.json")]) == 0
    assert cli.main(["lint", str(workspace / "resume.json"), "--strict"]) == 1


# ── the deliverable's name ────────────────────────────────────────────────────

def test_publishing_matches_a_name_already_in_the_folder(tmp_path, resume):
    """Publishing must not invent a second naming convention.

    A workspace may already call its deliverable something this tool would not
    have chosen. Writing under a different name does not replace it — it leaves
    two resumes side by side, one of them stale, which is exactly the "which file
    do I send?" confusion publishing exists to end.
    """
    from career_docs import deliverable
    for suffix in (".pdf", ".html", ".md"):
        (tmp_path / f"Resume_Smith{suffix}").write_text("old", encoding="utf-8")

    assert deliverable.existing_stem(tmp_path) == "Resume_Smith"
    assert deliverable.default_stem(resume, tmp_path) == "Resume_Smith"


def test_an_empty_folder_gets_the_derived_name(tmp_path, resume):
    from career_docs import deliverable
    assert deliverable.existing_stem(tmp_path) is None
    assert deliverable.default_stem(resume, tmp_path) == "Smith_Resume"


def test_an_ambiguous_folder_falls_back_to_the_derived_name(tmp_path, resume):
    """Two complete trios: no way to tell which is *the* deliverable."""
    from career_docs import deliverable
    for stem in ("Resume_Smith", "Smith_CV"):
        for suffix in (".pdf", ".html", ".md"):
            (tmp_path / f"{stem}{suffix}").write_text("x", encoding="utf-8")
    assert deliverable.existing_stem(tmp_path) is None
    assert deliverable.default_stem(resume, tmp_path) == "Smith_Resume"


def test_a_partial_trio_is_not_a_deliverable(tmp_path, resume):
    from career_docs import deliverable
    (tmp_path / "Stray.pdf").write_text("x", encoding="utf-8")
    assert deliverable.existing_stem(tmp_path) is None


# ── the tool works without a workspace ────────────────────────────────────────

def test_publish_works_with_a_bare_profile_and_no_init(tmp_path, data, monkeypatch):
    """`init` is optional. A lone resume.json anywhere must still publish.

    Publishing writes beside the profile it found — wherever that is — so the
    answer to "where does publish go if init was never run" is: next to your
    resume.json, not into some workspace that does not exist.
    """
    monkeypatch.setattr("career_docs.pdf.write",
                        lambda html, path, **kw: path.write_bytes(b"%PDF-fake"))
    loose = tmp_path / "somewhere"
    loose.mkdir()
    (loose / "resume.json").write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.chdir(loose)
    monkeypatch.delenv("CAREER_DOCS_RESUME", raising=False)

    assert cli.main(["publish", "--theme", "default"]) == 0
    for suffix in (".pdf", ".html", ".md"):
        assert (loose / f"Smith_Resume{suffix}").exists()
