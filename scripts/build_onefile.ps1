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
        # Using -ErrorAction Continue so we can give a better message if it fails
        try {
            Remove-Item -Recurse -Force $folder -ErrorAction Stop
        } catch {
            Write-Host "Warning: Could not remove folder '$folder'. If a file is in use, please close it and try again." -ForegroundColor Red
            Write-Host "Error details: $($_.Exception.Message)" -ForegroundColor Red
            # If we can't clean dist/build, we probably shouldn't proceed
            exit 1
        }
    }
}

# 3) Ensure uv is available
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv not found. Please install uv first (https://github.com/astral-sh/uv)."
}

# 4) Sync dependencies
Write-Host "Syncing dependencies with uv..." -ForegroundColor Cyan
uv sync --dev

# --- Automatic Version Bumping ---
Write-Host "Updating version number..." -ForegroundColor Yellow
$pyprojectPath = "pyproject.toml"
$versionInfoPath = "packaging/pyinstaller/version_info.txt"

# Read version from pyproject.toml
$content = Get-Content $pyprojectPath -Raw
if ($content -match 'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"') {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    $patch = [int]$Matches[3]
    
    $newPatch = $patch + 1
    $newVersion = "$major.$minor.$newPatch"
    
    Write-Host "Incrementing version: $major.$minor.$patch -> $newVersion" -ForegroundColor Green
    
    # Update pyproject.toml
    $newContent = $content -replace 'version\s*=\s*"\d+\.\d+\.\d+"', "version = `"$newVersion`""
    $newContent | Set-Content $pyprojectPath -NoNewline
    
    # Update version_info.txt
    if (Test-Path $versionInfoPath) {
        $vInfo = Get-Content $versionInfoPath -Raw
        # Update tuples: (0, 2, 10, 0)
        $vInfo = $vInfo -replace 'filevers=\(\d+, \d+, \d+, \d+\)', "filevers=($major, $minor, $newPatch, 0)"
        $vInfo = $vInfo -replace 'prodvers=\(\d+, \d+, \d+, \d+\)', "prodvers=($major, $minor, $newPatch, 0)"
        # Update strings: u'0.2.10'
        $vInfo = $vInfo -replace "u'\d+\.\d+\.\d+'", "u'$newVersion'"
        $vInfo | Set-Content $versionInfoPath -NoNewline
    }
} else {
    Write-Host "Warning: Could not parse version from pyproject.toml. Skipping auto-bump." -ForegroundColor Red
}

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
