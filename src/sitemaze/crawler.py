"""Polite BFS HTML crawler — fallback when no sitemap or OpenAPI spec exists."""

from __future__ import annotations

import random
import time
from collections import deque
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from sitemaze.parsers import urls_to_graph

DEFAULT_DELAY_MIN = 0.5
DEFAULT_DELAY_MAX = 2.0
DEFAULT_MAX_DEPTH = 5
DEFAULT_MAX_PAGES = 500


def _fetch_robots(session: requests.Session, base_url: str) -> RobotFileParser:
    rp = RobotFileParser()
    robots_url = urljoin(base_url, "/robots.txt")
    timeout = getattr(session, "_sitemaze_timeout", 15)
    try:
        resp = session.get(robots_url, timeout=timeout)
        rp.parse(resp.text.splitlines())
    except Exception:
        pass
    rp.set_url(robots_url)
    return rp


def crawl(
    base_url: str,
    session: requests.Session,
    *,
    max_depth: int = DEFAULT_MAX_DEPTH,
    max_pages: int = DEFAULT_MAX_PAGES,
    delay_min: float = DEFAULT_DELAY_MIN,
    delay_max: float = DEFAULT_DELAY_MAX,
    emit=None,
) -> dict:
    """BFS crawl starting from base_url.

    Args:
        base_url:   The root URL to crawl.
        session:    Auth-configured requests.Session.
        max_depth:  Maximum link depth to follow.
        max_pages:  Maximum pages to visit.
        delay_min:  Minimum delay between requests (seconds).
        delay_max:  Maximum delay between requests (seconds).
        emit:       Optional callable(str) for progress messages (SSE).

    Returns:
        {"nodes": [...], "edges": [...]}
    """
    base_url = base_url.rstrip("/")
    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc
    timeout = getattr(session, "_sitemaze_timeout", 15)

    def log(msg: str):
        if emit:
            emit(msg)

    log(f"> Starting HTML crawler on {base_url}")
    rp = _fetch_robots(session, base_url)
    ua = session.headers.get("User-Agent", "*")

    visited: set[str] = set()
    discovered_urls: list[str] = []

    # Queue: (url, depth)
    queue: deque[tuple[str, int]] = deque()
    queue.append((base_url, 0))
    visited.add(base_url)

    while queue and len(discovered_urls) < max_pages:
        url, depth = queue.popleft()

        # Robots check
        if not rp.can_fetch(ua, url):
            log(f"  ⊘ Skipped (robots.txt): {url}")
            continue

        try:
            resp = session.get(url, timeout=timeout, allow_redirects=True)
        except Exception as exc:
            log(f"  ✗ Error fetching {url}: {exc}")
            continue

        if resp.status_code != 200:
            log(f"  ✗ HTTP {resp.status_code}: {url}")
            continue

        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            continue

        discovered_urls.append(url)
        pct = int(len(discovered_urls) / max_pages * 100)
        log(f"  ✓ [{len(discovered_urls)}/{max_pages}] {url}")

        if depth < max_depth:
            soup = BeautifulSoup(resp.text, "lxml")
            for tag in soup.find_all("a", href=True):
                href = tag["href"]
                abs_url = urljoin(url, href)
                # Normalise — strip fragment and trailing slash
                abs_parsed = urlparse(abs_url)
                abs_clean = abs_parsed._replace(fragment="").geturl().rstrip("/")

                # Same domain only
                if abs_parsed.netloc != base_domain:
                    continue
                # HTTP/HTTPS only
                if abs_parsed.scheme not in ("http", "https"):
                    continue
                if abs_clean not in visited:
                    visited.add(abs_clean)
                    queue.append((abs_clean, depth + 1))

        # Polite delay
        time.sleep(random.uniform(delay_min, delay_max))

    log(f"> Crawl complete — {len(discovered_urls)} pages found")
    return urls_to_graph(discovered_urls, base_url)
