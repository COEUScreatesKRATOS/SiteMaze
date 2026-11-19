"""JSON cache — read/write graph data per domain."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

# Cache directory relative to the package's working directory
_CACHE_DIR = Path("cache")


def _domain_slug(url: str) -> str:
    """Convert a URL to a safe filename slug."""
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    # Replace anything non-alphanumeric (except dots/hyphens) with underscore
    slug = re.sub(r"[^\w.\-]", "_", domain)
    return slug or "unknown"


def cache_path(url: str) -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR / f"{_domain_slug(url)}.json"


def save(url: str, graph: dict) -> Path:
    """Persist graph data to cache/{domain}.json. Returns the path."""
    path = cache_path(url)
    with path.open("w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)
    return path


def load(url: str) -> dict | None:
    """Load cached graph for url, or None if not cached."""
    path = cache_path(url)
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_from_file(path: str | Path) -> dict:
    """Load graph data from an arbitrary JSON file path."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def list_cached() -> list[dict]:
    """Return metadata for all cached domains."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    result = []
    for p in sorted(_CACHE_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            nodes = data.get("nodes", [])
            edges = data.get("edges", [])
            root = next((n for n in nodes if n.get("depth") == 0), None)
            result.append({
                "file": p.name,
                "domain": p.stem,
                "url": root["url"] if root else "",
                "nodes": len(nodes),
                "edges": len(edges),
            })
        except Exception:
            pass
    return result
