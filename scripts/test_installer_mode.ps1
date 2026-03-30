<#
.SYNOPSIS
    Tests ParrotInk installer behavior to verify SILENT mode works correctly.

.DESCRIPTION
    Run this BEFORE and AFTER recompiling the .iss fix to verify:
    1. Does /SILENT suppress the wizard pages? (or does the full wizard appear?)
    2. Does ShouldDelayLaunchAndSilent fire and write to the log?
#>
param(
    [switch]$Silent,   # Run in /SILENT mode (simulates tray update flow)
    [switch]$Full      # Run without flags (simulates fresh manual install)
)

$InstallerPath = Join-Path $PSScriptRoot "..\dist\ParrotInk-Setup.exe"
$InstallerPath = [System.IO.Path]::GetFullPath($InstallerPath)

if (-not (Test-Path $InstallerPath)) {
    Write-Host "ERROR: Installer not found at: $InstallerPath" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "ParrotInk Installer Mode Test" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan
Write-Host "Installer: $InstallerPath"
Write-Host ""

# ── Test 1: SILENT mode (what the tray update does) ──────────────────────────
if ($Silent -or (-not $Full)) {
    Write-Host "TEST 1: SILENT mode  (simulating in-app tray update)" -ForegroundColor Yellow
    Write-Host "       Launching with: /SILENT /pid=0"
    Write-Host ""
    Write-Host "WATCH THE UI carefully:" -ForegroundColor White
    Write-Host "  - If you see ONLY a progress bar with no Next/Back/Finish pages → SILENT is working ✓"
    Write-Host "  - If you see a FULL WIZARD with Next → Finish buttons            → SILENT is broken ✗"
    Write-Host ""
    Read-Host "Press Enter to launch the installer in SILENT mode"

    Start-Process -FilePath $InstallerPath -ArgumentList "/SILENT /pid=0" -Wait

    Write-Host ""
    Write-Host "Installer closed. Checking log..." -ForegroundColor Cyan

    $Log = Get-ChildItem -Path $env:TEMP -Filter "Setup Log *.txt" |
           Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-5) } |
           Sort-Object LastWriteTime -Descending |
           Select-Object -First 1

    if ($Log) {
        Write-Host "Log file: $($Log.FullName)" -ForegroundColor Gray

        $WizardSilentLine = Select-String -Path $Log.FullName -Pattern "WizardSilent|ShouldDelayLaunch|Delaying post-install"
        $InitLine         = Select-String -Path $Log.FullName -Pattern "Installer received PID|No PID passed"
        $RunLine          = Select-String -Path $Log.FullName -Pattern "\[Run\]"

        Write-Host ""
        Write-Host "--- Relevant log entries ---" -ForegroundColor DarkGray

        if ($InitLine) {
            Write-Host "  InitializeSetup : $($InitLine.Line.Trim())" -ForegroundColor Gray
        }
        if ($WizardSilentLine) {
            Write-Host "  Delay function  : $($WizardSilentLine.Line.Trim())" -ForegroundColor Green
            Write-Host ""
            Write-Host "RESULT: Delay fix FIRED correctly ✓" -ForegroundColor Green
        } else {
            Write-Host "  Delay function  : (not found in log)" -ForegroundColor Red
            Write-Host ""
            Write-Host "RESULT: Delay fix did NOT fire." -ForegroundColor Red
            Write-Host "        → Either SILENT mode is not being applied (WizardSilent()=False)," -ForegroundColor Red
            Write-Host "          or the installer was compiled before the fix was added." -ForegroundColor Red
        }

        Write-Host ""
        Write-Host "To open the full log: notepad '$($Log.FullName)'" -ForegroundColor Gray
    } else {
        Write-Host "No Setup Log found in TEMP. Is SetupLogging=yes in the .iss file?" -ForegroundColor Red
        Write-Host "(SetupLogging=yes was added by the fix — recompile first if missing)" -ForegroundColor Yellow
    }
}

# ── Test 2: Full wizard mode (normal manual install) ─────────────────────────
if ($Full) {
    Write-Host ""
    Write-Host "TEST 2: Full Wizard mode  (simulating fresh manual install)" -ForegroundColor Yellow
    Write-Host "       Launching with: no flags"
    Write-Host ""
    Write-Host "EXPECTED: Full wizard with Welcome → Install → Finish pages"
    Write-Host "          Finish page should have a checkbox to launch ParrotInk"
    Write-Host ""
    Read-Host "Press Enter to launch the installer in Full Wizard mode"

    Start-Process -FilePath $InstallerPath -Wait

    Write-Host ""
    Write-Host "Done. Did you see the full wizard with a Finish+launch checkbox? (that is correct)" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Test complete." -ForegroundColor Cyan
