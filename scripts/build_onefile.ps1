$ErrorActionPreference = "Stop"

# --- Configuration ---
$APP_NAME = "ParrotInk"
$SPEC_FILE = "packaging/pyinstaller/parrotink_onefile.spec"

# 1) Go to repo root
$repoRoot = (Split-Path -Parent $PSScriptRoot)
Set-Location $repoRoot
Write-Host "Repo root: $repoRoot" -ForegroundColor Cyan

# 2) Clean old outputs
Write-Host "Checking for running instances of $APP_NAME..." -ForegroundColor Yellow
$runningProcesses = Get-Process -Name $APP_NAME -ErrorAction SilentlyContinue
if ($runningProcesses) {
    Write-Host "Stopping running instances of $APP_NAME..." -ForegroundColor Yellow
    $runningProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1 # Give it a moment to release file handles
}

Write-Host "Cleaning previous build artifacts..." -ForegroundColor Yellow
$tempFolders = @("dist", "build")
foreach ($folder in $tempFolders) {
    if (Test-Path -Path $folder) {
        try {
            Remove-Item -Recurse -Force $folder -ErrorAction Stop
        } catch {
            Write-Host "Warning: Could not remove folder '$folder'. If a file is in use, please close it and try again." -ForegroundColor Red
            Write-Host "Error details: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    }
}

# 3) Ensure uv is available
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv not found. Please install uv first (https://github.com/astral-sh/uv)."
}

# 4) Sync dependencies (locked)
Write-Host "Syncing dependencies with uv..." -ForegroundColor Cyan
uv sync --locked --dev

# 5) Build
Write-Host "Starting PyInstaller build (onefile)..." -ForegroundColor Magenta
if (-not (Test-Path $SPEC_FILE)) {
    throw "Spec file not found at: $SPEC_FILE"
}

# We run pyinstaller through 'uv run' to use the synced environment
uv run pyinstaller --clean --noconfirm $SPEC_FILE

$exePath = "dist/$APP_NAME.exe"
if (Test-Path $exePath) {
    Write-Host "`nBuild Successful!" -ForegroundColor Green
    Write-Host "Artifact location: $exePath" -ForegroundColor Green
} else {
    Write-Host "`nBuild Failed: Artifact not found at $exePath" -ForegroundColor Red
    exit 1
}
