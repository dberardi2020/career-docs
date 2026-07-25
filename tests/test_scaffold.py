"""The workspace `init` scaffolds, and the promises its text makes.

The last two tests are the interesting ones. The scaffold ships prose telling a
newcomer which commands to run — and that prose had been documenting `build` and
`themes` (deleted) and `--theme slate` (a palette, not a layout), so a fresh `init`
handed people a quickstart that errored. Documentation drifting out of the code is
the failure mode this file exists to catch, since nothing else would.
"""
from __future__ import annotations

import re

import pytest

from career_docs import cli, compose, scaffold, space

WRITTEN = ("CLAUDE.md", "README.md",
           ".claude/skills/career-resume-update/SKILL.md",
           ".claude/skills/career-layouts-browse/SKILL.md",
           "Resume/resume.json")
FOLDERS = ("Resume/Archive", "Cover Letters", "Applications", "Reference")

SHIPPED_TEXT = (scaffold.WORKSPACE_CLAUDE_MD, scaffold.SKILL_RESUME_UPDATE_MD,
                scaffold.SKILL_LAYOUTS_BROWSE_MD, scaffold.WORKSPACE_README)
SHIPPED_IDS = ("claude_md", "resume_update_skill", "layouts_browse_skill", "readme")


@pytest.fixture
def workspace(tmp_path):
    scaffold.init(tmp_path)
    return tmp_path


def test_init_writes_the_workspace(workspace):
    for relative in WRITTEN:
        assert (workspace / relative).is_file(), relative
    for relative in FOLDERS:
        assert (workspace / relative).is_dir(), relative


def test_init_never_overwrites(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("mine", encoding="utf-8")
    scaffold.init(tmp_path)
    assert (tmp_path / "CLAUDE.md").read_text() == "mine"


def test_init_reports_what_it_skipped(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("mine", encoding="utf-8")
    assert any("skip" in line and "CLAUDE.md" in line
               for line in scaffold.init(tmp_path))


def test_skill_only_installs_just_the_skills(tmp_path):
    scaffold.init(tmp_path, skill_only=True)
    assert (tmp_path / ".claude/skills/career-resume-update/SKILL.md").is_file()
    assert (tmp_path / ".claude/skills/career-layouts-browse/SKILL.md").is_file()
    assert not (tmp_path / "CLAUDE.md").exists()
    assert not (tmp_path / "Resume").exists()


def test_skill_only_refreshes_a_stale_skill(tmp_path):
    """`init --skill-only` is the re-sync button: it overwrites the skills (which
    carry no user data) so a workspace cannot drift from the shipped version."""
    skill = tmp_path / ".claude/skills/career-resume-update/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("stale: career-docs build --theme all", encoding="utf-8")
    scaffold.init(tmp_path, skill_only=True)
    assert skill.read_text() == scaffold.SKILL_RESUME_UPDATE_MD


def test_init_does_not_overwrite_skills_without_skill_only(tmp_path):
    """A full init still never clobbers an existing file."""
    skill = tmp_path / ".claude/skills/career-resume-update/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("mine", encoding="utf-8")
    scaffold.init(tmp_path)
    assert skill.read_text() == "mine"


def test_no_double_clickable_launcher(workspace):
    """Dropped deliberately: it opens a Terminal window nobody asked for."""
    assert list(workspace.glob("*.command")) == []


def test_the_starter_resume_loads_and_lints(workspace):
    from career_docs import lint, model
    resume = model.load(workspace / "Resume" / "resume.json")
    lint.check(resume)  # must not raise on the thing we ship


def test_the_scaffold_is_generic(workspace):
    """Nothing personal may reach a shipped template.

    URLs are stripped before scanning: the repo's own GitHub address contains the
    author's surname and belongs in a template that points people back at the
    project. Prose naming a person or an employer does not.
    """
    for relative in WRITTEN:
        text = re.sub(r"https?://\S+", "", (workspace / relative).read_text()).lower()
        for leak in ("dimitri", "berardi", "kahuna", "building36", "savant"):
            assert leak not in text, f"{relative} mentions {leak}"


def test_the_scaffold_makes_no_assumptions_about_the_reader():
    """The skill describes a stranger; gendered pronouns do not belong in it."""
    for text in SHIPPED_TEXT:
        words = re.findall(r"\b\w+\b", text.lower())
        for pronoun in ("he", "him", "his", "she", "her", "hers"):
            assert pronoun not in words, f"shipped text says {pronoun!r}"


# ── the docs-match-the-code tests ─────────────────────────────────────────────

def _commands() -> set[str]:
    import argparse
    parser = cli.build_parser()
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return set(action.choices)
    raise AssertionError("no subcommands found")


@pytest.mark.parametrize("text", SHIPPED_TEXT, ids=SHIPPED_IDS)
def test_every_documented_command_exists(text):
    documented = set(re.findall(r"career-docs\s+([a-z-]+)", text))
    unknown = documented - _commands()
    assert not unknown, f"documented but not implemented: {sorted(unknown)}"


@pytest.mark.parametrize("text", SHIPPED_TEXT, ids=SHIPPED_IDS)
def test_every_documented_theme_resolves(text):
    """`publish --theme slate` used to be shipped advice, and it errored."""
    for value in re.findall(r"--theme\s+([a-z0-9-]+)", text):
        if value.startswith("<"):
            continue
        assert compose.preset(value) or space.parse(value), \
            f"--theme {value} is neither a preset nor a layout id"
