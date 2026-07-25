#!/usr/bin/env python3
"""Render the Career Docs docs from Markdown to styled HTML.

The docs follow a MD + HTML lock-step convention: the `.md` is the source of
truth, the `.html` is a styled human-review render of the same content. This is
the tool that produces the render — run it after editing any paired `.md`:

    python docs/render.py docs/tickets/tickets.md

Each `name.md` is written next to it as `name.html`, wrapped in a shared,
theme-aware CSS template (light/dark via prefers-color-scheme).

Handles the Markdown subset the docs use: ATX headings, paragraphs,
unordered/ordered lists (with lazy + indented continuation lines), GFM pipe
tables, blockquotes, fenced code, `---` rules, and inline code/bold/italic/links.
No third-party dependencies (stdlib only).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HEAD = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>
:root{{--bg:#fbfbfa;--fg:#22201d;--muted:#6b6862;--line:#e6e3dd;--code-bg:#f0eee9;--accent:#b5651d;--link:#a1571a}}
@media(prefers-color-scheme:dark){{:root{{--bg:#1a1917;--fg:#e6e3dd;--muted:#9a968e;--line:#332f2a;--code-bg:#26241f;--accent:#d99a5b;--link:#e0a866}}}}
*{{box-sizing:border-box}}
body{{background:var(--bg);color:var(--fg);font:16px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;margin:0}}
.wrap{{max-width:760px;margin:0 auto;padding:64px 28px 120px}}
h1{{font-size:2rem;line-height:1.2;margin:0 0 .3em;letter-spacing:-.02em}}
h2{{font-size:1.35rem;margin:2.2em 0 .5em;padding-bottom:.25em;border-bottom:1px solid var(--line)}}
h3{{font-size:1.08rem;margin:1.8em 0 .4em}}
h1,h2,h3,h4,h5,h6{{scroll-margin-top:1.2em}}
p{{margin:.7em 0}}
a{{color:var(--link);text-decoration:none;border-bottom:1px solid transparent}}
a:hover{{border-bottom-color:var(--link)}}
code{{background:var(--code-bg);padding:.12em .4em;border-radius:4px;font:.86em/1.4 ui-monospace,SFMono-Regular,Menlo,monospace}}
pre{{background:var(--code-bg);padding:16px 18px;border-radius:8px;overflow-x:auto;border:1px solid var(--line)}}
pre code{{background:none;padding:0;font-size:.85em}}
ul,ol{{padding-left:1.4em;margin:.7em 0}}
li{{margin:.3em 0}}
blockquote{{margin:1em 0;padding:.6em 1.1em;border-left:3px solid var(--accent);background:var(--code-bg);border-radius:0 6px 6px 0;color:var(--muted)}}
blockquote strong{{color:var(--fg)}}
.tablewrap{{overflow-x:auto;margin:1.1em 0}}
table{{border-collapse:collapse;width:100%;font-size:.92em}}
th,td{{border:1px solid var(--line);padding:.5em .7em;text-align:left;vertical-align:top}}
td:first-child{{white-space:nowrap}}
th{{background:var(--code-bg);font-weight:600}}
hr{{border:none;border-top:1px solid var(--line);margin:2em 0}}
strong{{font-weight:650}}
</style></head><body><main class="wrap">
'''
FOOT = '\n</main></body></html>\n'


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def slug(text: str) -> str:
    """A URL fragment from heading prose — inline markup stripped, links reduced to
    their label, everything else lowercased and hyphenated."""
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # links -> label
    t = re.sub(r"[`*_]", "", t)                        # inline markup
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def inline(text: str) -> str:
    # 1) pull out code spans so their contents are never touched by other rules
    spans: list[str] = []

    def stash(m):
        spans.append(m.group(1))
        return f"\x00{len(spans) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    # 2) escape the remaining literal text
    text = esc(text)
    # 3) links [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                  lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', text)
    # 4) bold, then italic. Bold may wrap an italic (`**a *b* c**`), so match the
    #    bold body non-greedily (it can contain single `*`) and resolve any italics
    #    inside it first; then italicise what remains. An italic wrapping a bold
    #    (`*a **b** c*`) falls out too, since the inner bold is consumed first.
    def italic(s: str) -> str:
        return re.sub(r"(?<!\*)\*(?!\*)([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    text = re.sub(r"\*\*(.+?)\*\*",
                  lambda m: f"<strong>{italic(m.group(1))}</strong>", text)
    text = italic(text)
    # 5) restore code spans (escaped)
    text = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{esc(spans[int(m.group(1))])}</code>", text)
    return text


def render_cells(row: str) -> list[str]:
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return [c.strip() for c in row.split("|")]


def is_sep(line: str) -> bool:
    return bool(re.match(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$", line)) and "-" in line


LIST_RE = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")


def render_blocks(lines: list[str]) -> list[str]:
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        # fenced code
        if line.lstrip().startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].lstrip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # closing fence
            out.append("<pre><code>" + esc("\n".join(buf)) + "</code></pre>")
            continue
        # heading
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            body = m.group(2).strip()
            # an explicit `{#custom-id}` wins over the auto-slug, so an anchor can
            # stay stable when the heading's wording changes
            anc = re.search(r"\s*\{#([A-Za-z0-9_-]+)\}\s*$", body)
            if anc:
                hid, body = anc.group(1), body[:anc.start()].rstrip()
            else:
                hid = slug(body)
            attr = f' id="{esc(hid)}"' if hid else ""
            out.append(f"<h{lvl}{attr}>{inline(body)}</h{lvl}>")
            i += 1
            continue
        # hr
        if re.match(r"^-{3,}\s*$", line):
            out.append("<hr>")
            i += 1
            continue
        # blockquote
        if line.lstrip().startswith(">"):
            buf = []
            while i < n and lines[i].lstrip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            inner = render_blocks(buf)
            out.append("<blockquote>\n" + "\n".join(inner) + "\n</blockquote>")
            continue
        # table: current line has a pipe and next line is a separator
        if "|" in line and i + 1 < n and is_sep(lines[i + 1]):
            header = render_cells(line)
            i += 2
            body = []
            while i < n and "|" in lines[i] and lines[i].strip():
                body.append(render_cells(lines[i]))
                i += 1
            th = "".join(f"<th>{inline(c)}</th>" for c in header)
            rows = []
            for r in body:
                tds = "".join(f"<td>{inline(c)}</td>" for c in r)
                rows.append(f"<tr>{tds}</tr>")
            out.append(f'<div class="tablewrap"><table><thead><tr>{th}</tr></thead><tbody>'
                       + "".join(rows) + "</tbody></table></div>")
            continue
        # list (ordered or unordered)
        m = LIST_RE.match(line)
        if m:
            ordered = m.group(2).endswith(".")
            items: list[str] = []
            cur: list[str] | None = None
            while i < n:
                lm = LIST_RE.match(lines[i])
                if lm:
                    if cur is not None:
                        items.append(" ".join(cur))
                    cur = [lm.group(3).strip()]
                    i += 1
                elif lines[i].strip() and not re.match(r"^(#{1,6}\s|```|-{3,}\s*$|>\s)", lines[i].lstrip()) and cur is not None:
                    # lazy / indented continuation of the current item
                    cur.append(lines[i].strip())
                    i += 1
                else:
                    break
            if cur is not None:
                items.append(" ".join(cur))
            tag = "ol" if ordered else "ul"
            lis = "".join(f"<li>{inline(it)}</li>" for it in items)
            out.append(f"<{tag}>{lis}</{tag}>")
            continue
        # paragraph
        buf = [line.strip()]
        i += 1
        while i < n and lines[i].strip() and not re.match(
                r"^(#{1,6}\s|```|>|-{3,}\s*$)", lines[i].lstrip()) \
                and not LIST_RE.match(lines[i]) \
                and not ("|" in lines[i] and i + 1 < n and is_sep(lines[i + 1])):
            buf.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(buf))}</p>")
    return out


def convert(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    # title = first H1
    title = md_path.stem
    for ln in lines:
        hm = re.match(r"^#\s+(.*)$", ln)
        if hm:
            t = re.sub(r"[*`]", "", hm.group(1)).strip()  # strip inline md for <title>
            title = esc(t)
            break
    body = "\n".join(render_blocks(lines))
    return HEAD.format(title=title) + body + FOOT


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    for arg in argv:
        p = Path(arg)
        p.with_suffix(".html").write_text(convert(p), encoding="utf-8")
        print(f"rendered {p} -> {p.with_suffix('.html').name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
