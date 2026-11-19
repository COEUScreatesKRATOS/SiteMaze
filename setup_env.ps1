$p = "c:\Users\chris.harding-brown\OneDrive - City of Dallas-5516124-G Tenant\Documents\Kiro\SiteMaze"
$python = "$p\.venv\Scripts\python.exe"
$pip    = "$p\.venv\Scripts\pip.exe"

Write-Host "==> Upgrading pip + setuptools..."
& $python -m pip install --upgrade pip setuptools wheel

Write-Host "==> Installing sitemaze..."
& $pip install -e $p

Write-Host "==> Installing pytest..."
& $pip install pytest

Write-Host "==> Running tests..."
& "$p\.venv\Scripts\pytest.exe" "$p\tests" -v
