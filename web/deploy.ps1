# One-click deploy: logs in to Cloudflare if needed, builds, and ships.
# Run from anywhere:  powershell -ExecutionPolicy Bypass -File .\deploy.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "1/3  checking Cloudflare login..." -ForegroundColor Cyan
npx wrangler whoami 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
	Write-Host "     not logged in, opening the browser..." -ForegroundColor Yellow
	npx wrangler login
}

Write-Host "2/3  building..." -ForegroundColor Cyan
npm run build
if ($LASTEXITCODE -ne 0) { throw "build failed" }

Write-Host "3/3  deploying..." -ForegroundColor Cyan
npx wrangler deploy
