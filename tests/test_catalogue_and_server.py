"""The two deliveries end to end: a folder you can open, and a server."""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from functools import partial
from http.server import ThreadingHTTPServer

import pytest

from career_docs import catalogue, compose, server, space


# ── catalogue ─────────────────────────────────────────────────────────────────

def test_catalogue_writes_a_page_per_layout_plus_an_index(tmp_path, resume):
    index, specs = catalogue.build(resume, 5, tmp_path)

    assert index == tmp_path / "index.html"
    assert index.exists()
    assert len(specs) == 5
    for spec in specs:
        assert (tmp_path / f"{spec.name}.html").exists()


def test_catalogue_is_reproducible(tmp_path, resume):
    a, _ = catalogue.build(resume, 4, tmp_path / "a")
    b, _ = catalogue.build(resume, 4, tmp_path / "b")
    assert a.read_text() == b.read_text()


def test_catalogue_options_json_is_agent_readable(tmp_path, resume):
    """An agent must be able to name a layout without parsing HTML."""
    _, specs = catalogue.build(resume, 5, tmp_path)
    payload = json.loads((tmp_path / "options.json").read_text())

    assert [o["name"] for o in payload["options"]] == [s.name for s in specs]
    assert not any("number" in o for o in payload["options"])
    for option in payload["options"]:
        assert (tmp_path / option["preview"]).exists()
        assert space.parse(option["name"]) is not None


def test_catalogue_previews_are_the_real_render(tmp_path, resume):
    _, specs = catalogue.build(resume, 3, tmp_path)
    for spec in specs:
        written = (tmp_path / f"{spec.name}.html").read_text()
        assert written == compose.render(resume, spec)


# ── server ────────────────────────────────────────────────────────────────────

@pytest.fixture
def live(tmp_path, resume, data):
    profile = tmp_path / "resume.json"
    profile.write_text(json.dumps(data), encoding="utf-8")
    ctx = {
        "resume": resume,
        "resume_path": profile,
        "stamp": profile.stat().st_mtime_ns,
        "count": 4,
        "out_dir": tmp_path / "out",
        "stem": "Test",
        "publish_dir": tmp_path / "workspace",
        "publish_stem": "Smith_Resume",
    }
    httpd = ThreadingHTTPServer(("127.0.0.1", 0),
                                partial(server.Handler, ctx=ctx))
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}", ctx
    httpd.shutdown()
    httpd.server_close()
    thread.join(timeout=5)


def get(url: str):
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.status, response.read().decode()


def test_root_serves_the_viewer(live):
    base, _ = live
    status, body = get(base + "/")
    assert status == 200
    assert body.startswith("<!doctype html>")
    assert 'const PREVIEW    = "route"' in body


def test_preview_renders_a_layout(live, resume):
    base, _ = live
    spec = space.page(0, 4)[0]
    status, body = get(f"{base}/preview/{spec.name}")
    assert status == 200
    assert body == compose.render(resume, spec)


def test_preview_of_an_unknown_layout_is_404(live):
    base, _ = live
    with pytest.raises(urllib.error.HTTPError) as exc:
        get(base + "/preview/harbor-321-mixed-compact")
    assert exc.value.code == 404


def test_unknown_route_is_404(live):
    base, _ = live
    with pytest.raises(urllib.error.HTTPError) as exc:
        get(base + "/nope")
    assert exc.value.code == 404


def test_the_server_keeps_no_session_state(live):
    """No favourites, no verdicts, no persisted batch — nothing to leak or sync."""
    base, ctx = live
    get(base + "/")
    get(base + "/")
    assert not any(p.name.endswith("session.json")
                   for p in ctx["out_dir"].glob("*") if p.is_file())
    # Config, not session: every key is fixed at startup and never mutated by a
    # request. Nothing here would need scoping to a user if this were hosted.
    assert set(ctx) == {"resume", "resume_path", "stamp", "count", "out_dir",
                        "stem", "publish_dir", "publish_stem"}


def post(base, path, payload):
    request = urllib.request.Request(
        base + path, method="POST", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def test_publish_writes_the_deliverable_beside_the_profile(live, monkeypatch):
    """Browsing has to be able to end in the file you send.

    Otherwise the last step is copying a name out of the page into a command,
    which was the half-finished handoff this replaces.
    """
    monkeypatch.setattr("career_docs.pdf.write",
                        lambda html, path, **kw: path.write_bytes(b"%PDF-fake"))
    base, ctx = live
    spec = space.page(0, 4)[0]

    result = post(base, "/api/publish", {"name": spec.name})

    assert result["ok"] is True
    assert result["stem"] == "Smith_Resume"
    for suffix in (".html", ".md", ".pdf"):
        assert (ctx["publish_dir"] / f"Smith_Resume{suffix}").exists()


def test_publish_never_writes_into_the_scratch_cache(live, monkeypatch):
    monkeypatch.setattr("career_docs.pdf.write",
                        lambda html, path, **kw: path.write_bytes(b"%PDF-fake"))
    base, ctx = live
    post(base, "/api/publish", {"name": space.page(0, 4)[0].name})
    assert not list(ctx["out_dir"].glob("*")) if ctx["out_dir"].exists() else True


def test_publish_rejects_an_unknown_layout(live):
    base, _ = live
    with pytest.raises(urllib.error.HTTPError) as exc:
        post(base, "/api/publish", {"name": "not-a-layout"})
    assert exc.value.code == 400


def test_export_rejects_an_unknown_layout(live):
    base, _ = live
    request = urllib.request.Request(
        base + "/api/export", method="POST",
        data=json.dumps({"name": "not-a-layout"}).encode(),
        headers={"Content-Type": "application/json"})
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(request, timeout=10)
    assert exc.value.code == 400


# ── paging ────────────────────────────────────────────────────────────────────

def test_pages_partition_the_space():
    """Every layout is reachable by paging, and no page repeats one."""
    count = 240
    seen = []
    for index in range(space.pages(count)):
        seen += [s.name for s in space.page(index, count)]
    assert len(seen) == len(set(seen)) == space.TOTAL


def test_paging_is_deterministic():
    assert [s.name for s in space.page(7, 12)] == [s.name for s in space.page(7, 12)]


def test_paging_wraps():
    assert space.page(space.pages(12), 12) == space.page(0, 12)


def test_a_page_is_not_all_one_palette():
    """Enumeration order clusters near-identical layouts; browse order must not."""
    palettes = {compose.PALETTES[s.palette][0] for s in space.page(0, 12)}
    assert len(palettes) >= 4


def test_the_page_route_serves_a_page(live):
    base, _ = live
    status, body = get(base + "/api/page?i=3")
    payload = json.loads(body)
    assert payload["index"] == 3
    assert payload["pages"] == space.pages(4)
    assert [o["name"] for o in payload["options"]] == [s.name for s in space.page(3, 4)]


def test_the_page_route_wraps_rather_than_erroring(live):
    base, _ = live
    payload = json.loads(get(base + f"/api/page?i={space.pages(4) + 1}")[1])
    assert payload["index"] == 1


# ── live reload ───────────────────────────────────────────────────────────────

def test_the_server_notices_the_profile_changing(live, data):
    """An agent edits the profile while the viewer is open. That is the premise.

    Caching a copy at startup meant serving a document that no longer existed —
    silently, which is worse than serving nothing.
    """
    base, ctx = live
    spec = space.page(0, 4)[0]
    assert "Northwind" in get(f"{base}/preview/{spec.name}")[1]

    edited = json.loads(json.dumps(data))
    edited["work"][0]["name"] = "Renamed Employer"
    ctx["resume_path"].write_text(json.dumps(edited), encoding="utf-8")
    import os
    os.utime(ctx["resume_path"], ns=(ctx["stamp"] + 10**9, ctx["stamp"] + 10**9))

    body = get(f"{base}/preview/{spec.name}")[1]
    assert "Renamed Employer" in body
    assert "Northwind" not in body


def test_a_broken_edit_keeps_serving_the_last_good_profile(live, ctx_break=None):
    """Caught mid-write, or saved invalid — do not blank the page."""
    base, ctx = live
    spec = space.page(0, 4)[0]
    ctx["resume_path"].write_text("{ not json", encoding="utf-8")
    import os
    os.utime(ctx["resume_path"], ns=(ctx["stamp"] + 10**9, ctx["stamp"] + 10**9))

    status, body = get(f"{base}/preview/{spec.name}")
    assert status == 200
    assert "Northwind" in body
