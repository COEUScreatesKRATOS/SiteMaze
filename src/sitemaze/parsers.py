"""Parsers for sitemap.xml and OpenAPI specs → normalised graph data."""

from __future__ import annotations

import json
import re
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# URL segment → CamelCase title
# ---------------------------------------------------------------------------

def segment_to_title(segment: str) -> str:
    """Convert a URL segment to a CamelCase display title.

    Examples:
        "fake-page"       → "FakePage"
        "some_page_name"  → "SomePageName"
        "test"            → "Test"
        "Index.htm"       → "Index"
        "some-page.html"  → "SomePage"
        ""                → "(root)"
    """
    if not segment:
        return "(root)"
    # Strip common file extensions before titling
    segment = re.sub(r"\.(html?|aspx?|php|jsp|cfm|xml|json)$", "", segment, flags=re.IGNORECASE)
    # Split on hyphens, underscores, dots, spaces
    words = re.split(r"[-_.\s]+", segment)
    return "".join(w.capitalize() for w in words if w)


# ---------------------------------------------------------------------------
# URL → node hierarchy
# ---------------------------------------------------------------------------

def urls_to_graph(urls: list[str], base_url: str) -> dict:
    """Convert a flat list of URLs into nodes + edges.

    Each unique URL path prefix becomes a node.
    Returns {"nodes": [...], "edges": [...]}.
    """
    parsed_base = urlparse(base_url.rstrip("/"))
    domain = parsed_base.netloc or parsed_base.path

    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    # Root node
    root_id = domain
    nodes[root_id] = {
        "id": root_id,
        "title": domain,
        "url": base_url,
        "depth": 0,
        "parent": None,
    }

    for url in urls:
        parsed = urlparse(url)
        # Skip external URLs
        if parsed.netloc and parsed.netloc != parsed_base.netloc:
            continue

        path = parsed.path.rstrip("/") or "/"
        segments = [s for s in path.split("/") if s]

        parent_id = root_id
        accumulated = ""

        for depth, segment in enumerate(segments, start=1):
            accumulated += f"/{segment}"
            node_id = f"{domain}{accumulated}"

            if node_id not in nodes:
                nodes[node_id] = {
                    "id": node_id,
                    "title": segment_to_title(segment),
                    "url": f"{parsed_base.scheme}://{domain}{accumulated}",
                    "depth": depth,
                    "parent": parent_id,
                }
                edges.append({"source": parent_id, "target": node_id})

            parent_id = node_id

    return {"nodes": list(nodes.values()), "edges": edges}


# ---------------------------------------------------------------------------
# Sitemap parser
# ---------------------------------------------------------------------------

def parse_sitemap(xml_text: str, base_url: str) -> dict:
    """Parse sitemap XML (urlset or sitemapindex) into graph data."""
    from xml.etree import ElementTree as ET

    ns_map = {
        "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
    }

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return {"nodes": [], "edges": [], "error": "Invalid sitemap XML"}

    tag = root.tag.lower()
    urls: list[str] = []

    # Strip namespace for tag comparison
    local_tag = re.sub(r"\{.*?\}", "", root.tag).lower()

    if local_tag == "urlset":
        for url_elem in root.iter():
            local = re.sub(r"\{.*?\}", "", url_elem.tag).lower()
            if local == "loc":
                loc = (url_elem.text or "").strip()
                if loc:
                    urls.append(loc)
    elif local_tag == "sitemapindex":
        # For sitemap indexes, treat each <loc> as a URL entry
        for elem in root.iter():
            local = re.sub(r"\{.*?\}", "", elem.tag).lower()
            if local == "loc":
                loc = (elem.text or "").strip()
                if loc:
                    urls.append(loc)

    return urls_to_graph(urls, base_url)


# ---------------------------------------------------------------------------
# OpenAPI parser
# ---------------------------------------------------------------------------

def parse_openapi(json_text: str, base_url: str) -> dict:
    """Parse an OpenAPI/Swagger JSON spec into graph data."""
    try:
        spec = json.loads(json_text)
    except json.JSONDecodeError:
        return {"nodes": [], "edges": [], "error": "Invalid JSON"}

    paths = spec.get("paths", {})
    urls = []

    # Determine server base from spec if available
    servers = spec.get("servers", [])
    if servers and isinstance(servers, list):
        server_url = servers[0].get("url", base_url)
    else:
        # Swagger 2.0
        host = spec.get("host", "")
        scheme = (spec.get("schemes") or ["https"])[0]
        base_path = spec.get("basePath", "")
        if host:
            server_url = f"{scheme}://{host}{base_path}"
        else:
            server_url = base_url

    for path in paths:
        full_url = server_url.rstrip("/") + path
        urls.append(full_url)

    return urls_to_graph(urls, server_url or base_url)
