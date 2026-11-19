"""CLI entry point for SiteMaze."""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sitemaze",
        description="SiteMaze — crawl any website as a living 3D knowledge graph.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sitemaze                        # Launch UI at http://localhost:5000
  sitemaze --port 8080            # Custom port
  sitemaze --no-browser           # Don't auto-open browser
  sitemaze --debug                # Flask debug mode
        """,
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=5000,
        help="Port to run the Flask server on (default: 5000)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the browser",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run Flask in debug mode",
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="%(prog)s 0.1.0",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    from sitemaze.server import create_app, run_server
    app = create_app()
    run_server(app, host=args.host, port=args.port, debug=args.debug, open_browser=not args.no_browser)


if __name__ == "__main__":
    main(sys.argv[1:])
