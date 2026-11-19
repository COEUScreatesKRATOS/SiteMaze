# SiteMaze — Code Standards & Information Architecture

These rules apply to every file in this project, every session, without exception.

---

## 1. Information Architecture — File & Folder Layout

Each file has one job. If you are unsure where code belongs, ask: "what is the single responsibility of this file?" and place it accordingly.

```
src/sitemaze/
├── __init__.py        # version + package identity only
├── __main__.py        # entry point shim only — calls cli.main()
├── cli.py             # argument parsing and orchestration only
├── server.py          # Flask app factory, routes, and SSE streaming
├── discovery.py       # probe sitemap / robots / OpenAPI — no parsing
├── parsers.py         # parse sitemap XML and OpenAPI into graph data
├── crawler.py         # BFS HTML crawl — no discovery, no parsing
├── session.py         # requests.Session factory — auth only
├── cache.py           # JSON read/write per domain — no business logic
└── frontend/
    ├── index.html     # landing page — URL input, drag-drop, advanced options
    └── graph.html     # 3D graph view — all graph interaction lives here
```

Never put business logic in `__init__.py`, `__main__.py`, or the frontend HTML files beyond what their role requires.

---

## 2. Naming Conventions

| Context | Form | Example |
|---|---|---|
| GitHub repo / UI / browser | `SiteMaze` | Logo, page title, README heading |
| Python package / import | `sitemaze` | `import sitemaze`, `pip install sitemaze` |
| CLI command | `sitemaze` | `sitemaze --port 8080` |
| Folder name | `sitemaze/` | `src/sitemaze/` |
| Functions / variables | `snake_case` | `build_session()`, `max_depth` |
| Classes | `PascalCase` | `GraphNode`, `CrawlResult` |
| Constants | `UPPER_SNAKE` | `DEFAULT_MAX_PAGES` |
| HTML ids / JS variables | `kebab-case` / `camelCase` | `#graph-wrap`, `visibleIds` |

One consistent term per concept throughout the codebase. Never introduce a synonym.

---

## 3. Code Organisation Within Files

Every Python file follows this order, with a blank line between each section:

1. Module docstring
2. `from __future__ import annotations`
3. Standard library imports
4. Third-party imports
5. Local imports
6. Module-level constants
7. Public functions / classes (alphabetical within logical groups)
8. Private helpers (`_prefixed`) at the bottom

Every function has:
- A one-line docstring stating what it returns or does
- Type hints on all parameters and return values
- No more than 40 lines of body — split into helpers if longer

---

## 4. Comments & Documentation

- Docstrings on every public function, class, and module
- Inline comments only for non-obvious logic — never restate what the code says
- Section dividers in long files use: `# ── Section Name ──────────`
- TODO format: `# TODO(username): description` — never leave bare `# TODO`

---

## 5. Frontend (HTML / JS)

Each HTML file is self-contained. Structure within the `<script>` block:

1. State variables (grouped, labelled with a section divider)
2. Initialisation / boot logic
3. Event handlers
4. Pure helper functions (alphabetical)
5. API calls

CSS custom properties (`--var`) for every colour and size. No hardcoded hex values outside `:root`. Dark and light theme tokens defined once at the top.

---

## 6. Error Handling

- Never swallow exceptions silently with a bare `except: pass`
- Log or re-raise with context: `except Exception as exc: log(f"✗ {exc}")`
- Flask routes return `{"error": "..."}` with an appropriate HTTP status — never a bare 500
- JS fetch calls always have a `.catch()` that shows the error to the user

---

## 7. Git Hygiene

- Commits are atomic: one logical change per commit
- Commit messages follow: `type: short description` where type is one of:
  `feat` `fix` `chore` `docs` `refactor` `test` `style`
- Never commit: cache files, `.env`, `__pycache__`, `.venv`, secrets, or personal data
- The `cache/` directory is gitignored — crawl results never enter the repo

---

## 8. Security

- Secrets and credentials go in environment variables — never hardcoded
- User-supplied URLs are validated before use: must start with `http://` or `https://`
- The crawler respects `robots.txt` without exception
- Flask runs on `127.0.0.1` by default — never `0.0.0.0` without explicit user opt-in
- No sensitive data (tokens, passwords, internal URLs) in logs or commit messages

---

## 9. Testing

- Every new function in `discovery.py`, `parsers.py`, `crawler.py`, or `session.py` gets a unit test
- Tests live in `tests/` mirroring the source file name: `test_parsers.py` tests `parsers.py`
- Tests are fast and use mocks for HTTP — no real network calls in the test suite
- Test names follow: `test_<function>_<scenario>` e.g. `test_parse_sitemap_bad_xml`

---

## 10. Developer Experience

When a developer opens any file they should be able to answer within 10 seconds:
- What does this file do?
- Where do I add X?
- What calls this, and what does it call?

If that is not true, the file needs to be refactored or documented.
