# SiteMaze — Code Audit Report

**Date:** 2025-07  
**Auditor:** Kiro code-audit agent  
**Scope:** All source files in `src/sitemaze/`, `tests/`, `.gitignore`, `pyproject.toml`

---

## Executive Summary

The codebase is in **good overall health**. The information architecture is sound — every file sticks to its declared responsibility — and the security posture is solid with no hardcoded secrets, correct Flask binding, and URL validation in place. The test suite covers the three most logic-heavy modules well.

The most critical outstanding issues are:

1. **Missing `test_crawler.py`** — `crawler.py` is a required-to-test module per the standards, and it has no test file at all.
2. **Silent exception swallowing** in `cache.py`, `crawler.py` (`_fetch_robots`), and `discovery.py` (`_get`) — bare `except: pass` patterns that hide real failures.
3. **Multiple missing docstrings** on public functions across `cli.py`, `cache.py`, and several route functions in `server.py`.
4. **Inline function-body imports** scattered throughout `server.py` and `parsers.py` break the prescribed section order and are unnecessary.
5. **Two unused imports** in `server.py` (`render_template_string`, `urlparse`) and one **unused local variable** in `parsers.py` (`tag`, `ns_map`).
6. **JS fetch `.catch()` missing** on `loadRecent()` in `index.html` — the error is silently swallowed.
7. **Version hardcoded** in `cli.py` as a string literal instead of referencing `__version__` from `__init__.py`.

---

## Per-File Findings

---

### `src/sitemaze/__init__.py`

**Overall: PASS** — no issues.

The file contains only the module docstring, `__version__`, and `__author__`. Fully compliant.

---

### `src/sitemaze/__main__.py`

**Overall: PASS** — no issues.

Calls `cli.main()` and nothing else. Fully compliant.

---

### `src/sitemaze/cli.py`

| # | Severity | Category | Description | Line | Fix |
|---|----------|----------|-------------|------|-----|
| 1 | MEDIUM | Documentation | `build_parser` has no docstring. All public functions require one. | 9 | Add `"""Return the configured ArgumentParser for the sitemaze CLI."""` |
| 2 | LOW | Code org | `main` has no docstring. | 51 | Add `"""Parse CLI arguments and start the Flask server."""` |
| 3 | LOW | Naming/DX | Version string `"%(prog)s 0.1.0"` is hardcoded. If the version in `pyproject.toml` or `__init__.py` changes, this string goes stale. | 46 | Import `__version__` from `sitemaze` and use `f"%(prog)s {__version__}"`. |

---

### `src/sitemaze/session.py`

**Overall: PASS** — no issues.

Both public functions have docstrings and type hints. Section order is correct. No silent exception handling. The `_sitemaze_timeout` attribute approach (with `# type: ignore`) is acceptable given the limitation of extending `requests.Session`.

---

### `src/sitemaze/cache.py`

| # | Severity | Category | Description | Line | Fix |
|---|----------|----------|-------------|------|-----|
| 1 | MEDIUM | Documentation | `cache_path` has no docstring. | 23 | Add `"""Return the cache file Path for the given URL, creating cache dir if needed."""` |
| 2 | HIGH | Error handling | `list_cached` swallows all exceptions silently with `except Exception: pass`. A corrupted file will cause the entry to be silently dropped with no log message. | 68 | Change to `except Exception as exc: continue` after adding a log call, or at minimum log the filename and error. Since `list_cached` is used in a web route that cannot emit, consider a `warnings.warn` or structured logging call. |
| 3 | LOW | Code org | `_CACHE_DIR` is a relative path (`Path("cache")`). This means the cache location changes depending on the process cwd, which may differ between `sitemaze` CLI invocations and test runs. | 11 | Anchor to the package root or make it configurable via an env var. |

---

### `src/sitemaze/discovery.py`

| # | Severity | Category | Description | Line | Fix |
|---|----------|----------|-------------|------|-----|
| 1 | HIGH | Error handling | `_get` swallows all exceptions silently with `except Exception: pass`. Network errors, SSL failures, and malformed URLs all vanish without a trace. | 17 | Add at minimum `except Exception as exc: pass  # logged by caller` with a note — but ideally log at DEBUG level before returning `None`. |
| 2 | LOW | Documentation | `_get` has no docstring (private helper, so LOW rather than MEDIUM, but standards require docstrings on all functions). | 11 | Add `"""Fetch url with the session; return Response on 200 or None."""` |
| 3 | LOW | Documentation | `_is_xml` and `_is_openapi` have no docstrings. | 23, 28 | Each needs a one-line docstring. |

---

### `src/sitemaze/parsers.py`

| # | Severity | Category | Description | Line | Fix |
|---|----------|----------|-------------|------|-----|
| 1 | MEDIUM | Code org | `from xml.etree import ElementTree as ET` is inside the body of `parse_sitemap` rather than at the top of the file. The standards require stdlib imports in the module-level import section. | 97 | Move to module-level stdlib import block. |
| 2 | LOW | Code quality | `tag = root.tag.lower()` on line 108 assigns a variable that is never read (the equivalent `local_tag` on line 112 is used instead). | 108 | Delete the `tag` assignment. |
| 3 | LOW | Code quality | `ns_map` dict on lines 99–102 is defined but never used anywhere in the function. | 99 | Delete the `ns_map` definition. |

---

### `src/sitemaze/crawler.py`

| # | Severity | Category | Description | Line | Fix |
|---|----------|----------|-------------|------|-----|
| 1 | HIGH | Error handling | `_fetch_robots` silently swallows all exceptions with `except Exception: pass`. If `robots.txt` fetch fails for any reason (network, SSL, encoding), the failure is invisible and the robot parser is left in an uninitialised state. | 29 | Log the failure: `except Exception as exc: log(f"⚠ robots.txt fetch failed: {exc}")` — but `_fetch_robots` does not receive `emit`, so at a minimum raise or return a permissive-by-default parser explicitly. |
| 2 | LOW | Documentation | `_fetch_robots` has no docstring. | 22 | Add `"""Fetch and parse robots.txt for base_url; returns a permissive parser on failure."""` |
| 3 | LOW | Code org | `crawl` body is 68 lines. The standards cap function bodies at 40 lines. | 35–102 | Extract the per-URL processing block (robots check → fetch → parse links) into a private helper `_process_page`. |

---

### `src/sitemaze/server.py`

| # | Severity | Category | Description | Line | Fix |
|---|----------|----------|-------------|------|-----|
| 1 | MEDIUM | Code org | `render_template_string` is imported from Flask but never used anywhere in the file. | 13 | Remove from the import line. |
| 2 | MEDIUM | Code org | `urlparse` is imported from `urllib.parse` but never used in `server.py` (the URL scheme check is done with `.startswith()` not `urlparse`). | 11 | Remove from the import line. |
| 3 | MEDIUM | Code org | `from sitemaze.cache import list_cached`, `from sitemaze.session import session_from_dict`, `from sitemaze import cache as _cache`, `from sitemaze import discovery as _disc`, `from sitemaze import parsers as _parsers`, `from sitemaze import crawler as _crawler`, `from sitemaze.cache import cache_path` are all deferred inside route functions or the `_run` thread function rather than declared at module level. This violates the prescribed section order. The circular-import concern that often motivates deferred imports does not apply here. | 49, 71, 91–94, 201 | Move all `from sitemaze.*` imports to the module-level local-imports section. |
| 4 | MEDIUM | Error handling | `json.JSONDecodeError` on line 188 (HTML import path) swallows the exception silently with `pass`, then returns a generic error. This loses the reason parsing failed. | 188 | At minimum capture and log the exception before returning the generic error. |
| 5 | LOW | Documentation | Route functions `index`, `graph`, `version`, `cached`, `crawl_endpoint`, `import_endpoint`, `export_json` have no docstrings. | 27, 31, 35, 38, 44 ff., 162 ff., 196 ff. | Add one-line docstrings to each route function. |
| 6 | LOW | Documentation | `_read_html` helper has no docstring. | 26 | Add `"""Read and return the named HTML file as a string."""` |
| 7 | LOW | Code org | The `generate()` / `_run()` nesting inside `crawl_endpoint` is 70+ lines. Extract `_run` to a module-level private function to keep route handlers under 40 lines. | 76–155 | Extract the crawl orchestration thread body into a private `_crawl_thread(url, session, max_depth, max_pages, q)` function. |
| 8 | LOW | Code org | `import re` inside the `import_endpoint` function body. | 183 | Move to module-level stdlib imports. |

---

### `src/sitemaze/frontend/index.html`

| # | Severity | Category | Description | Line | Fix |
|---|----------|----------|-------------|------|-----|
| 1 | HIGH | Error handling | `loadRecent()` ends with `} catch {}` — the network/JSON error is silently discarded. The standards require all JS fetch calls to have a `.catch()` that shows the error to the user. | 524 | Change the empty catch to `catch (e) { console.warn('Recent sites load failed:', e); }` (since failing to load recents is non-critical, a console warning is acceptable, but the exception must not be swallowed entirely). |
| 2 | MEDIUM | Error handling | `startCrawl` → `try { auth.extra_headers = JSON.parse(headersRaw); } catch {}` on line 485 silently ignores a JSON parse failure on user-supplied input. The user gets no feedback that their headers JSON is invalid. | 485 | Add an alert or inline error: `catch { alert('Extra Headers must be valid JSON.'); return; }` |
| 3 | LOW | Frontend structure | The script block order broadly follows the standard (state vars, init/boot, event handlers, helpers, API calls) but `loadRecent` and `updateExploreBtn` are called at the bottom of the script _after_ the event-handler section. This is acceptable as boot-time calls, but the placement could be cleaner by grouping them under an explicit init section. | End of script | Move `loadRecent()` and `updateExploreBtn()` calls into an explicit `// ── Boot ──` section. |
| 4 | LOW | CSS | `color: #000` is hardcoded in `.explore-btn` for the button text. | ~184 | Add `--btn-text: #000` to `:root` and use `color: var(--btn-text)`. The light theme also uses `#000` so a single token suffices. |

---

### `src/sitemaze/frontend/graph.html`

| # | Severity | Category | Description | Line | Fix |
|---|----------|----------|-------------|------|-----|
| 1 | HIGH | Error handling | `pump()` has an empty `catch {}` on line 760 that swallows JSON parse errors on individual SSE frames. If a malformed event arrives, it fails silently and the UI stalls. | 760 | Change to `catch (e) { appendLog('⚠ Parse error: ' + e.message, 'err'); }` |
| 2 | HIGH | Error handling | `window.addEventListener('load', ...)` boot block has `try { loadGraph(JSON.parse(stored)); return; } catch {}` that silently discards a corrupted `sessionStorage` entry. The user sees the loading overlay indefinitely. | 791 | Change to `catch (e) { appendLog('⚠ Stored graph is corrupt: ' + e.message, 'err'); }` and fall through to the crawl path. |
| 3 | MEDIUM | Frontend structure | `DEPTH_COLORS` and `PATH_COLORS` are plain JS arrays with hardcoded hex strings. The standards say CSS custom properties for all colours. These colours also need to match the graph background which is determined by `--bg`. | State section | Define `--depth-color-0` through `--depth-color-7` and `--path-color-0` through `--path-color-9` in `:root`, then read them in JS with `getComputedStyle(document.documentElement).getPropertyValue('--depth-color-0')`. Alternatively, keep them in JS but add a `// NOTE: intentionally not in CSS — 3d-force-graph does not read CSS vars` comment. |
| 4 | MEDIUM | Frontend structure | `nodeLabel` on line ~638 uses a hardcoded inline style string with hex colours (`#111`, `#333`, `#e8e8e8`, `#00b4ff`). These are not CSS custom properties and do not adapt to the light theme. | ~638 | Inject the CSS variable values at render time: read `--bg2`, `--border`, `--text`, `--accent` with `getComputedStyle` and interpolate into the template string. |
| 5 | LOW | Frontend structure | `setColorMode` and `setSizeMode` use `onclick="..."` inline event handlers on `div` elements (the `.toggle-opt` buttons). The standards prefer `addEventListener`. | HTML | Convert to `addEventListener('click', ...)` in the script block. |
| 6 | LOW | CSS | Several `px` values in the CSS (`48px`, `260px`, `220px`) are literal dimensions that could be CSS custom properties for easier resizing. The standards say CSS custom properties for all sizes. The `--panel-w` and `--toolbar-w` tokens already exist — the topbar height (`48px`) is used in multiple places without a token. | CSS | Add `--topbar-h: 48px` to `:root` and replace all literal `48px` usages. |

---

### `tests/__init__.py`

**Overall: PASS** — empty file, correct.

---

### `tests/test_session.py`

**Overall: PASS** — no issues.

Good coverage of `build_session` and `session_from_dict`. All test names follow `test_<function>_<scenario>`. No real network calls. `from __future__ import annotations` is absent, but test files are not required to follow the same section order as production modules.

---

### `tests/test_parsers.py`

| # | Severity | Category | Description | Line | Fix |
|---|----------|----------|-------------|------|-----|
| 1 | LOW | Testing | `import pytest` is present but `pytest` is never used (no `@pytest.mark` or `pytest.raises`). | 3 | Remove the unused import. |
| 2 | LOW | Testing | There is no test for `parse_sitemap` with a `sitemapindex` root element (index vs. urlset). | — | Add `test_parse_sitemap_sitemapindex` to cover the other branch in `parse_sitemap`. |
| 3 | LOW | Testing | No test covers `segment_to_title` with a file extension that should be stripped (e.g., `"about.html"` → `"About"`). | — | Add `test_segment_strips_extension`. |

---

### `tests/test_discovery.py`

| # | Severity | Category | Description | Line | Fix |
|---|----------|----------|-------------|------|-----|
| 1 | MEDIUM | Testing | `_mock_session` replaces `session.get` with a plain function. This means the `allow_redirects` kwarg is passed through without issue, but it also means `session.headers.get("User-Agent")` still returns the real user-agent — and since `discover` reads it via `session.headers.get(...)`, the mock is slightly incomplete. This is a minor correctness gap rather than a failing test. | 10–19 | Low priority; note in a comment or use `MagicMock` for the entire session. |
| 2 | LOW | Testing | There is no test for `discover` when `robots.txt` lists a sitemap URL that then returns a 404 or non-XML. | — | Add `test_discover_robots_sitemap_unreachable`. |

---

### `tests/` — MISSING FILE

| # | Severity | Category | Description | Fix |
|---|----------|----------|-------------|-----|
| 1 | HIGH | Testing | **`test_crawler.py` does not exist.** The standards require a unit test file for every module in `discovery.py`, `parsers.py`, `crawler.py`, and `session.py`. `crawler.py` is entirely untested. | Create `tests/test_crawler.py` covering: `_fetch_robots` with a mocked session, `crawl` with a mock returning one HTML page, `crawl` with a robots.txt that disallows the target URL, and `crawl` stopping at `max_pages`. |

---

### `.gitignore`

**Overall: PASS with one minor gap.**

| # | Severity | Category | Description | Fix |
|---|----------|----------|-------------|-----|
| 1 | LOW | Git hygiene | The `.gitignore` excludes `.kiro/` ✓, `cache/` ✓, `__pycache__/` ✓, `.env` ✓, `.venv/` ✓. However, it does not explicitly ignore `*.pyc` files in nested directories — the pattern `*.py[cod]` covers `.pyc`, `.pyo`, `.pyd` at any depth, so this is covered. No action required. |
| 2 | LOW | Git hygiene | The `.gitignore` excludes all `.ps1` files, which means legitimate PowerShell scripts added to the repo (e.g., a `Makefile` equivalent) would also be excluded. This is probably intentional given the comment, but worth documenting. | Add a comment: `# This excludes ALL .ps1 files; re-add specific scripts with !script.ps1 if needed.` |

---

### `pyproject.toml`

**Overall: PASS** — no issues.

Dependencies are pinned to minimum versions (`flask>=3.0`, `requests>=2.31`, `beautifulsoup4>=4.12`, `lxml>=5.0`), which is appropriate for a library. The `[project.scripts]` entry is correct. `pytest` is not listed as a dev dependency, which means contributors must know to install it separately — consider adding a `[project.optional-dependencies]` dev section.

---

## Prioritised Fix List

### HIGH — fix before next commit

| Priority | File | Issue |
|---|---|---|
| H-1 | `tests/` | Create `tests/test_crawler.py` — `crawler.py` is entirely untested |
| H-2 | `cache.py` line 68 | `list_cached` silently swallows file parse errors; at minimum log them |
| H-3 | `discovery.py` line 17 | `_get` swallows all network exceptions silently |
| H-4 | `crawler.py` line 29 | `_fetch_robots` swallows all fetch exceptions silently |
| H-5 | `graph.html` line 760 | Empty `catch {}` in SSE `pump()` — parse errors vanish, UI stalls |
| H-6 | `graph.html` line 791 | Empty `catch {}` on `JSON.parse(stored)` — corrupted state causes infinite loading overlay |
| H-7 | `index.html` line 524 | `loadRecent` empty `catch {}` — errors silently discarded |

### MEDIUM — fix in next cleanup pass

| Priority | File | Issue |
|---|---|---|
| M-1 | `server.py` line 13 | Remove unused `render_template_string` import |
| M-2 | `server.py` line 11 | Remove unused `urlparse` import |
| M-3 | `server.py` lines 49, 71, 91–94, 201 | Move all deferred local imports to module-level |
| M-4 | `server.py` line 188 | `json.JSONDecodeError` silently swallowed in HTML import path |
| M-5 | `parsers.py` line 97 | Move `from xml.etree import ElementTree as ET` to module-level |
| M-6 | `cli.py` line 9 | Add docstring to `build_parser` |
| M-7 | `cache.py` line 23 | Add docstring to `cache_path` |
| M-8 | `index.html` line 485 | `JSON.parse` failure on extra-headers input silently swallowed |
| M-9 | `graph.html` ~line 638 | Node label inline styles use hardcoded hex — not theme-aware |
| M-10 | `graph.html` state section | `DEPTH_COLORS`/`PATH_COLORS` hardcoded hex not in CSS vars (or add explanatory comment) |

### LOW — tidy up when convenient

| Priority | File | Issue |
|---|---|---|
| L-1 | `cli.py` line 46 | Hardcoded version string — use `__version__` |
| L-2 | `cli.py` line 51 | Missing docstring on `main` |
| L-3 | `parsers.py` line 108 | Unused `tag` variable |
| L-4 | `parsers.py` lines 99–102 | Unused `ns_map` dict |
| L-5 | `discovery.py` lines 11, 23, 28 | Missing docstrings on `_get`, `_is_xml`, `_is_openapi` |
| L-6 | `crawler.py` line 22 | Missing docstring on `_fetch_robots` |
| L-7 | `crawler.py` lines 35–102 | `crawl` body is ~68 lines — extract inner loop into `_process_page` helper |
| L-8 | `server.py` line 183 | `import re` inside function body — move to module level |
| L-9 | `server.py` lines 27 ff. | Missing docstrings on all route functions and `_read_html` |
| L-10 | `server.py` lines 76–155 | `_run` thread body is 50+ lines inside a route — extract to `_crawl_thread` |
| L-11 | `graph.html` | `48px` topbar height repeated without a CSS custom property |
| L-12 | `graph.html` | `setColorMode`/`setSizeMode` wired via `onclick=` inline attributes — use `addEventListener` |
| L-13 | `index.html` line ~184 | `color: #000` hardcoded — add `--btn-text` token |
| L-14 | `tests/test_parsers.py` line 3 | Unused `import pytest` |
| L-15 | `tests/test_parsers.py` | Missing tests: `sitemapindex` branch, extension stripping |
| L-16 | `tests/test_discovery.py` | Missing test: robots.txt sitemap URL returns 404 |
| L-17 | `pyproject.toml` | No dev dependency group — add `[project.optional-dependencies] dev = ["pytest>=8", "pytest-mock"]` |
| L-18 | `cache.py` line 11 | Relative `Path("cache")` ties cache location to process cwd |
