$ErrorActionPreference = "Continue"

$repoRoot = (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot

Write-Host "Cleaning build, dist, and __pycache__..." -ForegroundColor Yellow

$targets = @("build/ParrotInk", "dist", "**/__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache")

foreach ($target in $targets) {
    if (Test-Path $target) {
        Write-Host "Removing $target"
        Remove-Item -Recurse -Force $target
    }
}

Write-Host "Done." -ForegroundColor Green
