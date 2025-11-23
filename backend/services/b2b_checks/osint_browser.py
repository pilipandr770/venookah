# file: backend/services/b2b_checks/osint_browser.py
"""
Helper to capture a website snapshot (screenshot) for OSINT.

Primary attempt: use Playwright (if installed). Falls back to saving raw HTML.
Returns dict with keys: success(bool), path(str), detail(str).
"""
from __future__ import annotations

import os
import time
import logging
from typing import Optional

from flask import current_app

LOG = logging.getLogger(__name__)


def capture_site_snapshot(url: str, subdir: str = "b2b_screenshots") -> dict:
    """Capture a screenshot of `url` and save under `static/uploads/<subdir>/`.

    Returns: {"success": bool, "path": relative_path_or_empty, "detail": message}
    """
    if not url:
        return {"success": False, "path": None, "detail": "No URL provided"}

    try:
        # Prepare output directory inside static/uploads
        uploads_dir = os.path.join(current_app.root_path, "static", "uploads", subdir)
        os.makedirs(uploads_dir, exist_ok=True)
        timestamp = int(time.time())
        safe_name = str(timestamp)
        png_path = os.path.join(uploads_dir, f"{safe_name}.png")

        # Try Playwright first
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_default_timeout(30000)
                try:
                    page.goto(url)
                except Exception:
                    # try adding http:// scheme
                    if not url.startswith("http"):
                        try:
                            page.goto("http://" + url)
                        except Exception as e:
                            LOG.exception("Playwright could not open URL")
                            browser.close()
                            return {"success": False, "path": None, "detail": f"Playwright open error: {e}"}

                # wait a short time for dynamic content
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass
                page.screenshot(path=png_path, full_page=True)
                browser.close()

            rel = os.path.relpath(png_path, os.path.join(current_app.root_path, "static"))
            return {"success": True, "path": f"/static/{rel.replace(os.path.sep, '/')}", "detail": "screenshot"}
        except Exception as e:
            LOG.info("Playwright unavailable or failed: %s", e)

        # Fallback: fetch HTML and save as .html file
        try:
            import requests
            from bs4 import BeautifulSoup

            r = requests.get(url if url.startswith("http") else ("http://" + url), timeout=15)
            html = r.text
            soup = BeautifulSoup(html, "html.parser")
            # Simple prettify to reduce size
            content = soup.prettify()
            html_path = os.path.join(uploads_dir, f"{safe_name}.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(content)
            rel = os.path.relpath(html_path, os.path.join(current_app.root_path, "static"))
            return {"success": True, "path": f"/static/{rel.replace(os.path.sep, '/')}", "detail": "html"}
        except Exception as e:
            LOG.exception("Fallback HTML snapshot failed")
            return {"success": False, "path": None, "detail": f"fallback error: {e}"}

    except Exception as e:
        LOG.exception("Unexpected error capturing site snapshot")
        return {"success": False, "path": None, "detail": str(e)}
