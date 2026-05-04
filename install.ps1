#Requires -Version 5.1
<#
.SYNOPSIS
  Trailarr installer bootstrap for Windows.

.DESCRIPTION
  Downloads the latest Trailarr release and launches the Python installer.
  Must be run as Administrator.

  Prerequisites: uv  (https://docs.astral.sh/uv/)
    Install with PowerShell:
      powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

.EXAMPLE
  # Run as Administrator:
  Set-ExecutionPolicy Bypass -Scope Process -Force
  .\install.ps1
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Capture script path at script scope before any function calls.
# $MyInvocation inside a function returns function context, not script path.
$ScriptFile = $PSCommandPath

$GitHubRepo   = 'nandyalu/trailarr'
$PythonVersion = '3.13'

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
function Write-Info    { param($m) Write-Host "  [>]  $m" -ForegroundColor Cyan }
function Write-Success { param($m) Write-Host "  [+]  $m" -ForegroundColor Green }
function Write-Warn    { param($m) Write-Host "  [!]  $m" -ForegroundColor Yellow }
function Write-Err     { param($m) Write-Host "  [x]  $m" -ForegroundColor Red }

function Write-Banner {
    Write-Host @'

 _____ ____      _    ___ _        _    ____  ____
|_   _|  _ \    / \  |_ _| |      / \  |  _ \|  _ \
  | | | |_) |  / _ \  | || |     / _ \ | |_) | |_) |
  | | |  _ <  / ___ \ | || |___ / ___ \|  _ <|  _ <
  |_| |_| \_\/_/   \_\___|_____/_/   \_\_| \_\_| \_\

'@ -ForegroundColor Cyan
    Write-Host "  Bootstrap Installer - Windows`n" -ForegroundColor Cyan
}

# --------------------------------------------------------------------------
# Re-launch as Administrator if needed
# --------------------------------------------------------------------------
function Ensure-Admin {
    $currentPrincipal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    $isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-Warn "Not running as Administrator - re-launching with elevation..."

        $scriptPath = $ScriptFile
        if (-not $scriptPath) {
            # Running via irm | iex - no file on disk.
            # Save the script to a temp file so we can re-launch it elevated.
            Write-Info "Saving installer to temp file for elevation..."
            $scriptPath = Join-Path $env:TEMP "trailarr-install.ps1"
            $rawUrl = "https://raw.githubusercontent.com/$GitHubRepo/main/install.ps1"
            try {
                Invoke-WebRequest -Uri $rawUrl -OutFile $scriptPath -UseBasicParsing
            } catch {
                Write-Err "Could not save installer to temp file: $_"
                Write-Host "`n  Run this in an elevated PowerShell instead:" -ForegroundColor White
                Write-Host "  irm $rawUrl | iex" -ForegroundColor Yellow
                Read-Host "`nPress Enter to close"
                exit 1
            }
        }

        Start-Process powershell.exe `
            -ArgumentList "-NoExit -NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`"" `
            -Verb RunAs
        # Don't call exit here - that would close the user's terminal when
        # run via irm | iex.  Just signal that elevation was handed off and
        # return so the caller can stop cleanly.
        Write-Success "Elevation requested. Please check the new PowerShell window."
        $script:ElevationLaunched = $true
        return
    }
    Write-Success "Running as Administrator"
}

# --------------------------------------------------------------------------
# Check prerequisites
# --------------------------------------------------------------------------
function Check-Uv {
    try {
        $uvVersion = & uv --version 2>&1
        Write-Success "uv found: $uvVersion"
    } catch {
        Write-Err "uv is not installed."
        Write-Host "`n  Install uv first (one command in PowerShell):" -ForegroundColor White
        Write-Host "    powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`"" `
            -ForegroundColor Yellow
        Write-Host "`n  Then re-run this installer.`n"
        exit 1
    }
}

# --------------------------------------------------------------------------
# Download latest release asset
# --------------------------------------------------------------------------
function Download-Release {
    Write-Info "Fetching latest release information..."

    $apiUrl = "https://api.github.com/repos/$GitHubRepo/releases/latest"
    try {
        $release = Invoke-RestMethod -Uri $apiUrl `
            -Headers @{ 'Accept' = 'application/vnd.github+json'; 'User-Agent' = 'trailarr-installer' } `
            -UseBasicParsing
    } catch {
        Write-Err "Failed to fetch release info: $_"
        exit 1
    }

    $script:AppVersion = $release.tag_name
    Write-Success "Latest version: $AppVersion"

    $asset = $release.assets | Where-Object { $_.name -like '*-release.tar.gz' } | Select-Object -First 1
    if (-not $asset) {
        Write-Err "No release asset found for version $AppVersion."
        Write-Host "  Check https://github.com/$GitHubRepo/releases for details."
        exit 1
    }

    $script:TempDir = Join-Path $env:TEMP "trailarr-install-$([System.IO.Path]::GetRandomFileName())"
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

    $archive = Join-Path $TempDir 'trailarr-release.tar.gz'
    Write-Info "Downloading $AppVersion..."

    try {
        $ProgressPreference = 'SilentlyContinue'   # Invoke-WebRequest is slow with progress
        Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $archive -UseBasicParsing
        $ProgressPreference = 'Continue'
    } catch {
        Write-Err "Download failed: $_"
        exit 1
    }
    Write-Success "Download complete"

    Write-Info "Extracting archive..."
    # Use tar (available in Windows 10 1803+)
    $extractDir = Join-Path $TempDir 'extracted'
    New-Item -ItemType Directory -Path $extractDir -Force | Out-Null
    & tar -xzf $archive -C $extractDir
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Extraction failed"
        exit 1
    }

    $script:SourceDir = Get-ChildItem -Path $extractDir -Directory | Select-Object -First 1 -ExpandProperty FullName
    if (-not $SourceDir) {
        Write-Err "Could not find extracted release directory"
        exit 1
    }
    Write-Success "Archive extracted"
}

# --------------------------------------------------------------------------
# Run the Python installer
# --------------------------------------------------------------------------
function Run-Installer {
    $installer = Join-Path $SourceDir 'scripts\install\install.py'

    if (-not (Test-Path $installer)) {
        Write-Err "Installer script not found at: $installer"
        exit 1
    }

    Write-Info "Launching Trailarr Python installer..."
    Write-Host ""

    & uv run `
        --python $PythonVersion `
        --with rich `
        --with tzlocal `
        $installer `
        --source-dir $SourceDir `
        --version $AppVersion

    if ($LASTEXITCODE -ne 0) {
        Write-Err "Installation failed (exit code $LASTEXITCODE)"
        exit $LASTEXITCODE
    }

    # Reload PATH from registry so trailarr commands work in this session
    # without requiring the user to open a new terminal.
    $machinePath = [System.Environment]::GetEnvironmentVariable('Path', 'Machine')
    $userPath    = [System.Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path    = ($machinePath, $userPath | Where-Object { $_ }) -join ';'
    Write-Info "PATH refreshed - trailarr commands are available in this terminal"
}

# --------------------------------------------------------------------------
# Cleanup
# --------------------------------------------------------------------------
function Cleanup {
    if ((Test-Path variable:script:TempDir) -and $script:TempDir -and (Test-Path $script:TempDir)) {
        Remove-Item -Recurse -Force $script:TempDir -ErrorAction SilentlyContinue
    }
}

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
try {
    Write-Banner
    Ensure-Admin
    # If elevation was handed off to a new window, stop here without
    # closing the terminal (return exits the script, not the host).
    if ((Test-Path variable:script:ElevationLaunched) -and $script:ElevationLaunched) { return }
    Check-Uv
    Download-Release
    Run-Installer
} catch {
    Write-Err "Unexpected error: $_"
    Read-Host "`nPress Enter to close"
    exit 1
} finally {
    Cleanup
}
