"""Auth-injectable requests.Session factory for SiteMaze."""

from __future__ import annotations

import requests

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def build_session(
    *,
    user_agent: str = DEFAULT_USER_AGENT,
    basic_user: str | None = None,
    basic_pass: str | None = None,
    bearer_token: str | None = None,
    cookies: dict[str, str] | None = None,
    extra_headers: dict[str, str] | None = None,
    timeout: int = 15,
) -> requests.Session:
    """Return a configured requests.Session.

    Auth priority: bearer_token > basic auth > cookies.
    All are optional and may be combined.
    """
    session = requests.Session()

    # Base headers
    session.headers.update({
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    })

    # Auth
    if bearer_token:
        session.headers["Authorization"] = f"Bearer {bearer_token}"
    elif basic_user and basic_pass:
        session.auth = (basic_user, basic_pass)

    if cookies:
        session.cookies.update(cookies)

    if extra_headers:
        session.headers.update(extra_headers)

    # Store timeout as attribute so callers can read it
    session._sitemaze_timeout = timeout  # type: ignore[attr-defined]

    return session


def session_from_dict(auth: dict) -> requests.Session:
    """Build a session from the JSON payload sent by the landing page form."""
    return build_session(
        basic_user=auth.get("basic_user") or None,
        basic_pass=auth.get("basic_pass") or None,
        bearer_token=auth.get("bearer_token") or None,
        cookies=auth.get("cookies") or None,
        extra_headers=auth.get("extra_headers") or None,
        timeout=int(auth.get("timeout", 15)),
    )
