"""Tests for session factory."""

from sitemaze.session import build_session, session_from_dict


def test_default_user_agent():
    s = build_session()
    assert "Mozilla" in s.headers["User-Agent"]


def test_bearer_token():
    s = build_session(bearer_token="mytoken")
    assert s.headers["Authorization"] == "Bearer mytoken"


def test_basic_auth():
    s = build_session(basic_user="user", basic_pass="pass")
    assert s.auth == ("user", "pass")


def test_cookies():
    s = build_session(cookies={"session": "abc123"})
    assert s.cookies.get("session") == "abc123"


def test_timeout_stored():
    s = build_session(timeout=30)
    assert s._sitemaze_timeout == 30


def test_session_from_dict_bearer():
    s = session_from_dict({"bearer_token": "tok"})
    assert "Bearer tok" in s.headers["Authorization"]


def test_session_from_dict_empty():
    s = session_from_dict({})
    assert s is not None
    assert "Mozilla" in s.headers["User-Agent"]
