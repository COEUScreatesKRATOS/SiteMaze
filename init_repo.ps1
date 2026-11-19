$root = "c:\Users\chris.harding-brown\OneDrive - City of Dallas-5516124-G Tenant\Documents\Kiro\SiteMaze"
Set-Location $root

Write-Host "==> Initialising git repo..."
git init -b main

Write-Host "==> Staging all files..."
git add .

Write-Host "==> Initial commit..."
git commit -m "feat: initial commit — SiteMaze v0.1.0

Full project scaffold per implementation plan:
- Flask server with SSE crawl streaming
- sitemap.xml / OpenAPI / BFS HTML crawler discovery
- 3D force-graph frontend (expand/collapse, inspector, toolbar)
- Dark + light theme, search highlight, color/size modes
- JSON cache, import/export
- Auth layer (bearer, basic, cookies)
- VS Code tasks.json + launch.json
- Unit tests (parsers, discovery, session)
- pyproject.toml, README, LICENSE (AGPL-3.0 + Commercial), CLA.md"

Write-Host "==> Adding remote origin..."
git remote add origin https://github.com/COEUScreatesKRATOS/SiteMaze.git

Write-Host "==> Pushing to GitHub..."
git push -u origin main

Write-Host "==> Done. Check https://github.com/COEUScreatesKRATOS/SiteMaze"
