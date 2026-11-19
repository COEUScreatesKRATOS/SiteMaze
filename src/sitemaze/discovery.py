"""Schema discovery: probe sitemap → robots.txt → OpenAPI before falling back to crawl."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import requests


def _get(session: requests.Session, url: str) -> requests.Response | None:
    timeout = getattr(session, "_sitemaze_timeout", 15)
    try:
        resp = session.get(url, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            return resp
    except Exception:
        pass
    return None


def _is_xml(content: str) -> bool:
    return "<urlset" in content or "<sitemapindex" in content


def _is_openapi(content: str) -> bool:
    return '"openapi"' in content or '"swagger"' in content or "'openapi'" in content


def discover(base_url: str, session: requests.Session, *, emit=None) -> dict:
    """Probe the base URL for a machine-readable schema.

    Returns:
        {
            "source": "sitemap" | "openapi" | "crawl_needed",
            "url": str,          # source URL (empty for crawl_needed)
            "data": str | None,  # raw response text
        }
    """
    base = base_url.rstrip("/")
    parsed = urlparse(base)
    if not parsed.scheme:
        base = "https://" + base
        parsed = urlparse(base)

    def log(msg: str):
        if emit:
            emit(msg)

    # 1. sitemap.xml directly
    for path in ["/sitemap.xml", "/sitemap_index.xml"]:
        url = urljoin(base, path)
        log(f"> Trying {url} ...")
        resp = _get(session, url)
        if resp and _is_xml(resp.text):
            log(f"  ✓ Found sitemap at {url}")
            return {"source": "sitemap", "url": url, "data": resp.text}

    # 2. robots.txt — look for Sitemap: directive
    robots_url = urljoin(base, "/robots.txt")
    log(f"> Trying {robots_url} ...")
    resp = _get(session, robots_url)
    if resp:
        for line in resp.text.splitlines():
            if line.lower().startswith("sitemap:"):
                sitemap_url = line.split(":", 1)[1].strip()
                log(f"  ✓ Found sitemap reference in robots.txt: {sitemap_url}")
                resp2 = _get(session, sitemap_url)
                if resp2 and _is_xml(resp2.text):
                    log(f"  ✓ Fetched sitemap from {sitemap_url}")
                    return {"source": "sitemap", "url": sitemap_url, "data": resp2.text}

    # 3. swagger.json / openapi.json
    for path in ["/swagger.json", "/openapi.json", "/api/swagger.json", "/api/openapi.json"]:
        url = urljoin(base, path)
        log(f"> Trying {url} ...")
        resp = _get(session, url)
        if resp and _is_openapi(resp.text):
            log(f"  ✓ Found OpenAPI spec at {url}")
            return {"source": "openapi", "url": url, "data": resp.text}

    log("> No sitemap or OpenAPI spec found — switching to HTML crawler")
    return {"source": "crawl_needed", "url": "", "data": None}
