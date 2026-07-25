"""A static, browsable catalogue of layouts.

`serve` is the same viewer with a process behind it. A catalogue needs no process:
it is a folder you open in a browser, commit, link, or hand to someone else — and a
`file://` path outlives a localhost URL.

It used to be a *lesser* viewer as well as a static one — a fixed spread of `count`
layouts with no filters and no paging, because a folder on disk has no backend to ask.
It no longer is: the index runs the same `embed` delivery the hosted demo does, so it
browses and filters all 10,080 client-side from the baked tables. What stays unique to
a catalogue is what it writes *beside* the index — a real render per spec, and
`options.json` — which is the part you can commit, link to, or hand to an agent.

The output is self-contained and works from `file://` — no server, no build step.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import compose, space, theme, viewer


def build(resume, count: int, out_dir: Path, source: Path | None = None) -> tuple[Path, list]:
    """Render `count` layouts plus an index. Returns (index path, specs).

    `count` is now two things at once, and deliberately: how many layouts get their
    own file on disk, and the index's page size. `source` is the profile's path, if known; the
    top bar is captioned with the workspace it names.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    specs = space.spread(count)

    for spec in specs:
        (out_dir / f"{spec.name}.html").write_text(
            compose.render(resume, spec), encoding="utf-8")

    data = viewer.bake(resume)
    index = out_dir / "index.html"
    index.write_text(
        viewer.page(specs, resume, preview="embed",
                    pages=space.pages(count), markups=data["markups"],
                    css=data["css"], count=count,
                    topbar=theme.local_nav(source),
                    footer=theme.footer()),
        encoding="utf-8")

    # The page is for a human; this is for the agent standing next to them, so a
    # layout can be named in conversation without parsing HTML. The spec name is
    # the handle — it is stable, decodable, and unique, which an ordinal is not.
    # These are the specs written to disk; the index itself browses all of them.
    (out_dir / "options.json").write_text(json.dumps({
        "options": [
            dict(preview=f"{s.name}.html", **viewer.describe(s)) for s in specs
        ],
    }, indent=2) + "\n", encoding="utf-8")
    return index, specs
