"""Print HTML to PDF using an installed Chrome, via its headless CLI.

Chrome has shipped `--headless --print-to-pdf` for years, which makes a browser
automation dependency (and the Node runtime under it) unnecessary — the whole
pipeline stays stdlib-plus-a-browser-you-already-have.

Chrome is located rather than configured. The original script hardcoded a Windows
path, which is precisely why it could not run on a Mac; discovery costs a few
lines and removes a whole class of "works on my machine".
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MAC = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
       "/Applications/Chromium.app/Contents/MacOS/Chromium",
       "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge")

WINDOWS = (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
           r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
           r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")

LINUX_NAMES = ("google-chrome", "google-chrome-stable", "chromium",
               "chromium-browser", "microsoft-edge")


class BrowserNotFound(RuntimeError):
    pass


def find_browser() -> str:
    """Locate a Chromium-family browser. `CAREER_DOCS_CHROME` wins if set."""
    if override := os.environ.get("CAREER_DOCS_CHROME"):
        if Path(override).exists():
            return override
        raise BrowserNotFound(
            f"CAREER_DOCS_CHROME points at {override!r}, which does not exist."
        )

    candidates = MAC if sys.platform == "darwin" else (
        WINDOWS if os.name == "nt" else ())
    for path in candidates:
        if Path(path).exists():
            return path
    for name in LINUX_NAMES:
        if found := shutil.which(name):
            return found

    raise BrowserNotFound(
        "No Chrome/Chromium/Edge found. Install one, or set "
        "CAREER_DOCS_CHROME to the executable."
    )


def write(html: str, out_path: str | Path, *, timeout: int = 60) -> Path:
    """Render `html` to a PDF at `out_path`. Returns the path written."""
    out_path = Path(out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    browser = find_browser()

    # Chrome writes the PDF relative to its own working directory in some
    # versions, and refuses to read HTML from stdin, so both sides go through
    # absolute paths in a scratch directory.
    with tempfile.TemporaryDirectory(prefix="career-docs-") as tmp:
        source = Path(tmp) / "resume.html"
        source.write_text(html, encoding="utf-8")
        cmd = [
            browser,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            # Page size and margins come from the theme's @page rule.
            f"--print-to-pdf={out_path}",
            source.as_uri(),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=timeout)

    # Chrome's exit code is not a reliable success signal across versions;
    # the artifact is.
    if not out_path.exists() or out_path.stat().st_size == 0:
        detail = (result.stderr or result.stdout or "").strip()[-800:]
        raise RuntimeError(
            f"Chrome produced no PDF (exit {result.returncode}).\n{detail}"
        )
    return out_path
