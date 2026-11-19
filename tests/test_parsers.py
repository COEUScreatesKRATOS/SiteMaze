"""Tests for sitemap and OpenAPI parsers."""

import json
import pytest

from sitemaze.parsers import segment_to_title, parse_sitemap, parse_openapi, urls_to_graph


# ── segment_to_title ─────────────────────────────────────────────────────

def test_segment_camel_hyphen():
    assert segment_to_title("fake-page") == "FakePage"

def test_segment_camel_underscore():
    assert segment_to_title("some_page_name") == "SomePageName"

def test_segment_single():
    assert segment_to_title("test") == "Test"

def test_segment_empty():
    assert segment_to_title("") == "(root)"

def test_segment_mixed():
    assert segment_to_title("some-page_name") == "SomePageName"


# ── urls_to_graph ─────────────────────────────────────────────────────────

SAMPLE_URLS = [
    "https://www.example.com/fake-page/test",
    "https://www.example.com/fake-page/test/some-page-name",
    "https://www.example.com/products",
    "https://www.example.com/products/shoes",
    "https://www.example.com/hr",
    "https://www.example.com/hr/portal",
]

def test_urls_to_graph_root():
    g = urls_to_graph(SAMPLE_URLS, "https://www.example.com")
    ids = {n["id"] for n in g["nodes"]}
    assert "www.example.com" in ids

def test_urls_to_graph_camel_titles():
    g = urls_to_graph(SAMPLE_URLS, "https://www.example.com")
    titles = {n["title"] for n in g["nodes"]}
    assert "FakePage" in titles
    assert "SomePageName" in titles

def test_urls_to_graph_depths():
    g = urls_to_graph(SAMPLE_URLS, "https://www.example.com")
    depth_map = {n["id"]: n["depth"] for n in g["nodes"]}
    assert depth_map["www.example.com"] == 0
    assert depth_map["www.example.com/hr"] == 1
    assert depth_map["www.example.com/hr/portal"] == 2

def test_urls_to_graph_edges():
    g = urls_to_graph(SAMPLE_URLS, "https://www.example.com")
    pairs = {(e["source"], e["target"]) for e in g["edges"]}
    assert ("www.example.com", "www.example.com/hr") in pairs
    assert ("www.example.com/hr", "www.example.com/hr/portal") in pairs


# ── parse_sitemap ─────────────────────────────────────────────────────────

SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://www.example.com/</loc></url>
  <url><loc>https://www.example.com/about</loc></url>
  <url><loc>https://www.example.com/products/shoes</loc></url>
</urlset>
"""

def test_parse_sitemap_node_count():
    g = parse_sitemap(SITEMAP_XML, "https://www.example.com")
    # root + about + products + shoes = 4
    assert len(g["nodes"]) == 4

def test_parse_sitemap_camel():
    g = parse_sitemap(SITEMAP_XML, "https://www.example.com")
    titles = {n["title"] for n in g["nodes"]}
    assert "About" in titles
    assert "Shoes" in titles

def test_parse_sitemap_bad_xml():
    g = parse_sitemap("<not xml", "https://www.example.com")
    assert g.get("error") is not None


# ── parse_openapi ─────────────────────────────────────────────────────────

OPENAPI_JSON = json.dumps({
    "openapi": "3.0.0",
    "info": {"title": "Test API", "version": "1.0"},
    "servers": [{"url": "https://api.example.com"}],
    "paths": {
        "/users": {},
        "/users/{id}": {},
        "/products/list": {},
    }
})

def test_parse_openapi_nodes():
    g = parse_openapi(OPENAPI_JSON, "https://api.example.com")
    ids = {n["id"] for n in g["nodes"]}
    assert "api.example.com/users" in ids

def test_parse_openapi_camel():
    g = parse_openapi(OPENAPI_JSON, "https://api.example.com")
    titles = {n["title"] for n in g["nodes"]}
    assert "Users" in titles
    assert "Products" in titles

def test_parse_openapi_bad_json():
    g = parse_openapi("{bad", "https://api.example.com")
    assert g.get("error") is not None
