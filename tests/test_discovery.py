"""Tests for schema discovery module (mocked HTTP)."""

from unittest.mock import MagicMock, patch

import pytest

from sitemaze.discovery import discover
from sitemaze.session import build_session


def _mock_session(responses: dict):
    """Return a session whose .get() returns mocked responses by URL."""
    session = build_session()

    def _get(url, **kwargs):
        resp = MagicMock()
        if url in responses:
            resp.status_code = 200
            resp.text = responses[url]
        else:
            resp.status_code = 404
            resp.text = ""
        return resp

    session.get = _get
    return session


SITEMAP_XML = """<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/page</loc></url>
</urlset>"""

ROBOTS_WITH_SITEMAP = "User-agent: *\nSitemap: https://example.com/sitemap.xml\n"
OPENAPI_JSON = '{"openapi":"3.0.0","paths":{"/test":{}}}'


def test_discover_sitemap_direct():
    session = _mock_session({"https://example.com/sitemap.xml": SITEMAP_XML})
    result = discover("https://example.com", session)
    assert result["source"] == "sitemap"
    assert result["url"] == "https://example.com/sitemap.xml"


def test_discover_sitemap_via_robots():
    session = _mock_session({
        "https://example.com/robots.txt": ROBOTS_WITH_SITEMAP,
        "https://example.com/sitemap.xml": SITEMAP_XML,
    })
    result = discover("https://example.com", session)
    assert result["source"] == "sitemap"


def test_discover_openapi():
    session = _mock_session({"https://example.com/openapi.json": OPENAPI_JSON})
    result = discover("https://example.com", session)
    assert result["source"] == "openapi"


def test_discover_crawl_needed():
    session = _mock_session({})  # all 404
    result = discover("https://example.com", session)
    assert result["source"] == "crawl_needed"
    assert result["url"] == ""
