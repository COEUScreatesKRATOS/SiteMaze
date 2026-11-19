"""Flask application — serves the UI and all API endpoints."""

from __future__ import annotations

import json
import os
import threading
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, Response, jsonify, render_template_string, request, stream_with_context

from sitemaze import __version__

FRONTEND_DIR = Path(__file__).parent / "frontend"


def create_app() -> Flask:
    app = Flask(__name__, static_folder=None)
    app.config["SECRET_KEY"] = os.urandom(24)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read_html(name: str) -> str:
        return (FRONTEND_DIR / name).read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @app.route("/")
    def index():
        return Response(_read_html("index.html"), mimetype="text/html")

    @app.route("/graph")
    def graph():
        return Response(_read_html("graph.html"), mimetype="text/html")

    @app.route("/api/version")
    def version():
        return jsonify({"version": __version__})

    @app.route("/api/cached")
    def cached():
        from sitemaze.cache import list_cached
        return jsonify(list_cached())

    # ------------------------------------------------------------------
    # POST /api/crawl  — start crawl, return SSE stream
    # ------------------------------------------------------------------

    @app.route("/api/crawl", methods=["POST"])
    def crawl_endpoint():
        body = request.get_json(force=True, silent=True) or {}
        url: str = (body.get("url") or "").strip()
        if not url:
            return jsonify({"error": "url is required"}), 400

        # Ensure scheme
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        auth_opts = body.get("auth", {})
        max_depth = int(body.get("max_depth", 5))
        max_pages = int(body.get("max_pages", 500))

        from sitemaze.session import session_from_dict
        session = session_from_dict(auth_opts)

        def generate():
            messages: list[str] = []
            graph_result: dict = {}

            def emit(msg: str):
                messages.append(msg)
                yield f"data: {json.dumps({'type': 'log', 'message': msg})}\n\n"

            # We need to actually iterate the generator inside here
            # Use a queue approach via inner function
            import queue as _queue
            q: _queue.Queue = _queue.Queue()

            def _emit(msg: str):
                q.put(("log", msg))

            def _run():
                from sitemaze import cache as _cache
                from sitemaze import discovery as _disc
                from sitemaze import parsers as _parsers
                from sitemaze import crawler as _crawler

                try:
                    # Check cache first
                    cached = _cache.load(url)
                    if cached:
                        q.put(("log", f"> Loaded from cache"))
                        q.put(("done", cached))
                        return

                    result = _disc.discover(url, session, emit=_emit)

                    if result["source"] == "sitemap":
                        q.put(("log", "> Parsing sitemap..."))
                        graph = _parsers.parse_sitemap(result["data"], url)
                    elif result["source"] == "openapi":
                        q.put(("log", "> Parsing OpenAPI spec..."))
                        graph = _parsers.parse_openapi(result["data"], url)
                    else:
                        graph = _crawler.crawl(
                            url, session,
                            max_depth=max_depth,
                            max_pages=max_pages,
                            emit=_emit,
                        )

                    nodes = graph.get("nodes", [])
                    edges = graph.get("edges", [])
                    q.put(("log", f"> ✓ {len(nodes)} nodes, {len(edges)} edges"))

                    path = _cache.save(url, graph)
                    q.put(("log", f"> Saved to {path}"))
                    q.put(("done", graph))

                except Exception as exc:
                    q.put(("error", str(exc)))

            thread = threading.Thread(target=_run, daemon=True)
            thread.start()

            while True:
                try:
                    item = q.get(timeout=60)
                except Exception:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Timeout'})}\n\n"
                    break

                kind, payload = item
                if kind == "log":
                    yield f"data: {json.dumps({'type': 'log', 'message': payload})}\n\n"
                elif kind == "done":
                    yield f"data: {json.dumps({'type': 'done', 'graph': payload})}\n\n"
                    break
                elif kind == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': payload})}\n\n"
                    break

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    # ------------------------------------------------------------------
    # POST /api/import  — load a JSON or HTML export
    # ------------------------------------------------------------------

    @app.route("/api/import", methods=["POST"])
    def import_endpoint():
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        f = request.files["file"]
        filename = f.filename or ""
        content = f.read().decode("utf-8", errors="replace")

        if filename.endswith(".json"):
            try:
                graph = json.loads(content)
                return jsonify({"graph": graph})
            except json.JSONDecodeError as e:
                return jsonify({"error": f"Invalid JSON: {e}"}), 400

        elif filename.endswith(".html"):
            # Extract embedded graph JSON from exported HTML
            import re
            m = re.search(r"window\.__SITEMAZE_GRAPH__\s*=\s*(\{.*?\});", content, re.DOTALL)
            if m:
                try:
                    graph = json.loads(m.group(1))
                    return jsonify({"graph": graph})
                except json.JSONDecodeError:
                    pass
            return jsonify({"error": "No graph data found in HTML file"}), 400

        return jsonify({"error": "Unsupported file type (use .json or .html)"}), 400

    # ------------------------------------------------------------------
    # GET /api/export/json  — download graph JSON
    # ------------------------------------------------------------------

    @app.route("/api/export/json")
    def export_json():
        domain = request.args.get("domain", "")
        from sitemaze.cache import cache_path
        path = cache_path(domain or "unknown")
        if not path.exists():
            return jsonify({"error": "No cached data for this domain"}), 404
        content = path.read_text(encoding="utf-8")
        return Response(
            content,
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment; filename={path.name}"},
        )

    return app


def run_server(
    app: Flask,
    *,
    host: str = "127.0.0.1",
    port: int = 5000,
    debug: bool = False,
    open_browser: bool = True,
) -> None:
    if open_browser and not debug:
        def _open():
            time.sleep(1.2)
            webbrowser.open(f"http://{host}:{port}")
        threading.Thread(target=_open, daemon=True).start()

    app.run(host=host, port=port, debug=debug, threaded=True)
