"""A local server for browsing the layout space.

The same viewer as the static catalogue, with two things a file on disk cannot do:
previews are rendered on request rather than written out ahead of time, and a layout
can be exported to PDF without leaving the page.

Rendering HTML is sub-millisecond, so there is no ceiling on how many layouts are
worth looking at — PDF is an export step for the one you chose, not a precondition
for looking at any of them.

There is deliberately no session: no favourites, no verdicts, no persisted batch.
The space is enumerable and has a deterministic browsing order, so "page 3" means
the same twelve layouts on every machine — the page index lives in the URL the
client asks for, not in state the server keeps.

The profile is re-read per request. It is expected to be edited *while* the viewer
is open, by an agent, which is the whole premise; a copy cached at startup means
watching a stale document and not knowing it.

Stdlib only — `http.server` is unglamorous, but this binds to loopback for one user.
"""
from __future__ import annotations

import json
import webbrowser
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from . import compose, deliverable, model, pdf, space, theme, viewer


class Handler(BaseHTTPRequestHandler):
    server_version = "resume-pipeline"

    def __init__(self, *args, ctx=None, **kwargs):
        self.ctx = ctx
        super().__init__(*args, **kwargs)

    # Quiet by default; a request log per preview is noise while browsing.
    def log_message(self, fmt, *args):
        pass

    def _send(self, body: bytes, ctype: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload, status: int = 200) -> None:
        self._send(json.dumps(payload).encode(), "application/json", status)

    def _resume(self):
        """The profile, re-read if it changed on disk.

        An agent is expected to be editing this while the viewer is open. A copy
        taken at startup means quietly showing a document that no longer exists,
        which is worse than showing nothing. Falls back to the last good copy if
        an edit is caught mid-write.
        """
        ctx = self.ctx
        path = ctx["resume_path"]
        try:
            stamp = path.stat().st_mtime_ns
        except OSError:
            return ctx["resume"]
        if stamp != ctx["stamp"]:
            try:
                ctx["resume"] = model.load(path)
                ctx["stamp"] = stamp
            except (model.ResumeError, OSError, ValueError):
                pass  # keep serving the last document that loaded
        return ctx["resume"]

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            return {}

    def do_GET(self):
        route = urlparse(self.path).path
        ctx = self.ctx

        if route == "/":
            html = viewer.page(space.page(0, ctx["count"]), self._resume(),
                               preview="route", exportable=True,
                               pages=space.pages(ctx["count"]),
                               topbar=theme.local_nav(ctx["resume_path"]),
                               footer=theme.footer())
            return self._send(html.encode(), "text/html; charset=utf-8")

        if route == "/api/page":
            query = parse_qs(urlparse(self.path).query)
            index = int((query.get("i") or ["0"])[0] or 0)
            # A filtered axis arrives as a query param named for the axis, repeated
            # once per selected value — `?palette=moss&palette=plum` is an OR within
            # the axis, and axes combine with AND. Paging then walks only matching
            # layouts rather than the whole space (RP-0033).
            #
            # Values are checked against the axis before use: an unknown one would
            # otherwise silently narrow the browse to nothing, which reads as "no
            # layouts exist" rather than "that filter is nonsense".
            filters = {}
            for axis, _ in space.AXES:
                wanted = [v for v in query.get(axis, []) if v in space.axis_values(axis)]
                if wanted:
                    filters[axis] = wanted
            total_pages = space.pages(ctx["count"], filters)
            specs = space.page(index, ctx["count"], filters)
            return self._json({
                "index": index % total_pages if total_pages else 0,
                "pages": total_pages,
                "total": space.total(filters),
                "options": [viewer.describe(s) for s in specs],
            })

        if route.startswith("/preview/"):
            spec = space.parse(unquote(route[len("/preview/"):]))
            if not spec:
                return self._send(b"unknown layout", "text/plain", 404)
            return self._send(compose.render(self._resume(), spec).encode(),
                              "text/html; charset=utf-8")

        return self._send(b"not found", "text/plain", 404)

    def do_POST(self):
        route = urlparse(self.path).path
        ctx = self.ctx

        if route == "/api/publish":
            # Browsing has to be able to end in the deliverable. Otherwise the
            # last step is copying a name out of the page and pasting it into a
            # command, which is the half-finished handoff this replaces.
            spec = space.parse(self._body().get("name") or "")
            if not spec:
                return self._json({"error": "unknown layout"}, 400)
            try:
                stem = deliverable.write(self._resume(), spec,
                                         ctx["publish_dir"], ctx["publish_stem"])
            except (pdf.BrowserNotFound, RuntimeError) as exc:
                return self._json({"error": str(exc)}, 500)
            return self._json({"ok": True, "stem": stem,
                               "dir": str(ctx["publish_dir"])})

        if route == "/api/export":
            spec = space.parse(self._body().get("name") or "")
            if not spec:
                return self._json({"error": "unknown layout"}, 400)
            out_dir = ctx["out_dir"]
            out_dir.mkdir(parents=True, exist_ok=True)
            html = compose.render(self._resume(), spec)
            target = out_dir / f"{ctx['stem']}.{spec.name}.pdf"
            try:
                pdf.write(html, target)
            except (pdf.BrowserNotFound, RuntimeError) as exc:
                return self._json({"error": str(exc)}, 500)
            (out_dir / f"{ctx['stem']}.{spec.name}.html").write_text(
                html, encoding="utf-8")
            return self._json({"ok": True, "path": str(target)})

        return self._json({"error": "not found"}, 404)


def serve(resume_path: Path, out_dir: Path, stem: str, count: int = 24,
          port: int = 8765, open_browser: bool = True,
          publish_stem: str | None = None) -> None:
    resume = model.load(resume_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    ctx = {
        "resume": resume,
        "resume_path": Path(resume_path),
        "stamp": Path(resume_path).stat().st_mtime_ns,
        "count": count,
        "out_dir": out_dir,            # scratch exports — the cache
        "stem": stem,
        # Publishing writes beside the profile, never into the cache: that is
        # the whole distinction between an export and the deliverable.
        "publish_dir": Path(resume_path).parent,
        "publish_stem": publish_stem or deliverable.default_stem(
            resume, Path(resume_path).parent),
    }
    httpd = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, ctx=ctx))
    url = f"http://127.0.0.1:{port}/"
    print(f"layout viewer running at {url}")
    print(f"  {space.TOTAL:,} layouts, {space.pages(count):,} pages of {count}")
    print("  ctrl-c to stop")
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
