# ◈ SiteMaze

> Crawl internal websites and visualize their page hierarchy and URL schema as an interactive, click-to-expand 3D knowledge graph.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey?logo=flask)
![License](https://img.shields.io/badge/License-AGPL--3.0%20%2B%20Commercial-purple)

---

## What it does

SiteMaze maps any website's structure into a live 3D force graph. Point it at a URL and it:

1. Looks for `sitemap.xml` (or a `Sitemap:` reference in `robots.txt`)
2. Falls back to `swagger.json` / `openapi.json`
3. Falls back to a polite BFS HTML crawler that respects `robots.txt` and adds randomised delays

Results are cached per domain and rendered in your browser with full rotate, zoom, expand/collapse, drag-to-pin, and search-highlight controls.

---

## Installation

```bash
# Clone
git clone https://github.com/YourUsername/SiteMaze.git
cd SiteMaze

# Create a virtual environment (Python 3.11+)
py -3.12 -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# Install
pip install -e .
```

---

## Usage

### Launch (auto-opens browser)
```bash
sitemaze
```

### Options
```
sitemaze --help

Options:
  --port, -p     Port (default 5000)
  --host         Host to bind (default 127.0.0.1)
  --no-browser   Don't auto-open the browser
  --debug        Flask debug mode
```

### Python module
```bash
python -m sitemaze
python -m sitemaze --port 8080 --debug
```

---

## VS Code / Kiro

Open the Command Palette → **Tasks: Run Task** → **Start SiteMaze**

For debugging: Run & Debug → **Debug SiteMaze**

---

## Graph controls

| Action | Result |
|---|---|
| **Double-click** node | Expand / collapse direct children |
| **Single-click** node | Open node inspector panel |
| **Drag** node | Pin node in 3D space |
| **Search bar** | Highlight matching nodes; dim others |
| **Color Mode** toggle | Depth colours vs path-based colours |
| **Node Size** toggle | Size by direct children vs all descendants |
| **Right toolbar** | Hover to open; click 🔒 to lock open |

---

## Discovery order

1. `{base}/sitemap.xml`
2. `{base}/robots.txt` → `Sitemap:` directive
3. `{base}/swagger.json`
4. `{base}/openapi.json`
5. BFS HTML crawler (polite — 0.5–2s delays, `robots.txt` respected)

---

## Project structure

```
SiteMaze/
├── pyproject.toml
├── README.md
├── LICENSE
├── CLA.md
├── .vscode/
│   ├── tasks.json
│   └── launch.json
├── cache/              ← per-domain JSON cache (gitignored)
├── tests/
└── src/
    └── sitemaze/
        ├── cli.py
        ├── server.py
        ├── discovery.py
        ├── parsers.py
        ├── crawler.py
        ├── session.py
        ├── cache.py
        └── frontend/
            ├── index.html
            └── graph.html
```

---

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Licensing

SiteMaze is dual-licensed:

- **Open source** — [GNU AGPL-3.0](LICENSE). Free to use, modify, and distribute under AGPL terms.
- **Commercial** — A separate commercial license is required for use in proprietary or SaaS products. Open a [GitHub Issue](https://github.com/YourUsername/SiteMaze/issues) to enquire.

### Contributing

By submitting a PR you agree to the [Contributor License Agreement](CLA.md). CLA compliance is checked automatically via [CLA Assistant](https://cla-assistant.io/).

---

## Topics

`python` `web-crawler` `sitemap` `visualization` `3d-force-graph` `flask` `cli` `developer-tools` `internal-tools` `site-architecture` `vscode`
