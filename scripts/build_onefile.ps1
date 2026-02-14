$ErrorActionPreference = "Stop"

# 1) Go to repo root
$repoRoot = (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot
Write-Host "Repo root: $repoRoot" -ForegroundColor Cyan

# 2) Clean old outputs
Write-Host "Cleaning previous build artifacts..." -ForegroundColor Yellow
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist"
}
if (Test-Path "build/pyinstaller/build") {
    # PyInstaller creates a 'build' folder inside the spec dir by default if not specified
    # but we will just clean the root build/ if it exists, excluding the spec file dir.
}

# Actually, let's just clean specific folders to avoid deleting the spec itself if it were in root build
if (Test-Path "build/Voice2Text") {
    Remove-Item -Recurse -Force "build/Voice2Text"
}

# 3) Ensure uv is available
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv not found. Please install uv first (https://github.com/astral-sh/uv)."
}

# 4) Sync dependencies
Write-Host "Syncing dependencies with uv..." -ForegroundColor Cyan
uv sync --dev

# 5) Build
Write-Host "Starting PyInstaller build (onefile)..." -ForegroundColor Magenta
# We run pyinstaller through 'uv run' to use the synced environment
uv run pyinstaller --clean --noconfirm build/pyinstaller/voice2text_onefile.spec

if (Test-Path "dist/Voice2Text.exe") {
    Write-Host "`nBuild Successful!" -ForegroundColor Green
    Write-Host "Artifact location: dist\Voice2Text.exe" -ForegroundColor Green
} else {
    Write-Host "`nBuild Failed: Artifact not found." -ForegroundColor Red
    exit 1
}
