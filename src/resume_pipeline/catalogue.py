"""A static, browsable catalogue of layouts.

`serve` is the same viewer with a process behind it. A catalogue needs no process:
it is a folder you open in a browser, commit, link, or hand to someone else — and a
`file://` path outlives a localhost URL.

The output is self-contained and works from `file://` — no server, no build step.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import compose, space, theme, viewer


def build(resume, count: int, out_dir: Path, source: str = "") -> tuple[Path, list]:
    """Render `count` layouts plus an index. Returns (index path, specs).

    `source` names the profile these came from; it captions the top bar.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    specs = space.spread(count)

    for spec in specs:
        (out_dir / f"{spec.name}.html").write_text(
            compose.render(resume, spec), encoding="utf-8")

    index = out_dir / "index.html"
    index.write_text(
        viewer.page(specs, resume, preview="file",
                    topbar=theme.local_nav(source or "resume.json"),
                    footer=theme.footer()),
        encoding="utf-8")

    # The page is for a human; this is for the agent standing next to them, so a
    # layout can be named in conversation without parsing HTML. The spec name is
    # the handle — it is stable, decodable, and unique, which an ordinal is not.
    (out_dir / "options.json").write_text(json.dumps({
        "options": [
            dict(preview=f"{s.name}.html", **viewer.describe(s)) for s in specs
        ],
    }, indent=2) + "\n", encoding="utf-8")
    return index, specs
