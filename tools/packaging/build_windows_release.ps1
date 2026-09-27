#requires -Version 5.1
<#
.SYNOPSIS
    Clean build of the MD Converter Windows release artifacts (P12-08).

.DESCRIPTION
    Implements the documented clean-build procedure from
    ``P12-08_SPECIFICATION_BASELINE`` section 9:

        source + configuration
            -> packaged application (PyInstaller, MD_Converter_Lite.spec)
            -> Windows installer   (Inno Setup, packaging/windows/MD_Converter.iss)

    The script only removes and recreates generated outputs (``build/``,
    ``dist/``, ``dist_installer/``); no source file is touched, and no manual
    post-build editing of ``dist/`` is required or performed by anyone.

    At the end it prints the release artifact inventory (path, size, SHA-256).

.PARAMETER SkipClean
    Rebuild without deleting the existing generated output directories.

.EXAMPLE
    powershell -File tools/packaging/build_windows_release.ps1
#>
[CmdletBinding()]
param(
    [switch]$SkipClean
)

$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
$Spec = 'MD_Converter_Lite.spec'
$InstallerScript = 'packaging\windows\MD_Converter.iss'
$InstallerOutput = Join-Path $RepoRoot 'dist_installer\MD_Converter_v1.1.0_Setup.exe'

function Write-Step {
    param([string]$Message)
    Write-Host ("[build] {0}" -f $Message)
}

function Remove-GeneratedPath {
    param([string]$Path)
    $resolved = [System.IO.Path]::GetFullPath($Path)
    $root = [System.IO.Path]::GetFullPath($RepoRoot)
    if (-not $resolved.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "refusing to remove '$resolved': outside the repository root"
    }
    $relative = $resolved.Substring($root.Length).TrimStart('\')
    $allowed = @(
        'build',
        'build\MD_Converter',
        'build\MD_Converter_Lite',
        'dist\MD_Converter',
        'dist\MD_Converter_Lite',
        'dist_installer\MD_Converter_v1.1.0_Setup.exe'
    )
    if ($allowed -notcontains $relative) {
        throw "refusing to remove '$relative': not a generated packaging output"
    }
    if (Test-Path -LiteralPath $resolved) {
        Write-Step ("removing generated output {0}" -f $relative)
        try {
            Remove-Item -LiteralPath $resolved -Recurse -Force -ErrorAction Stop
        } catch {
            # Historical release bundles that share these directories may be
            # protected by the environment; a failure here is reported, never
            # silently ignored, and only the packaging outputs matter.
            Write-Warning ("could not remove {0}: {1}" -f $relative, $_.Exception.Message)
        }
    }
}

function Get-InnoCompiler {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 7\ISCC.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe'),
        'C:\Program Files (x86)\Inno Setup 7\ISCC.exe',
        'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
        'C:\Program Files\Inno Setup 7\ISCC.exe',
        'C:\Program Files\Inno Setup 6\ISCC.exe'
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) { return $candidate }
    }
    $command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    throw 'Inno Setup compiler (ISCC.exe) was not found'
}

if (-not (Test-Path -LiteralPath $Python)) {
    throw "the project virtual environment is missing: $Python"
}

if (-not $SkipClean) {
    foreach ($relative in @(
            'build',
            'build\MD_Converter',
            'build\MD_Converter_Lite',
            'dist\MD_Converter',
            'dist\MD_Converter_Lite',
            'dist_installer\MD_Converter_v1.1.0_Setup.exe'
        )) {
        Remove-GeneratedPath -Path (Join-Path $RepoRoot $relative)
    }
}

# ---------------------------------------------------------------------------
# 1. Packaged application
# ---------------------------------------------------------------------------
Write-Step ("PyInstaller: {0}" -f $Spec)
Push-Location $RepoRoot
try {
    & $Python -m PyInstaller $Spec --noconfirm --log-level WARN
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}

$executable = Join-Path $RepoRoot 'dist\MD_Converter_Lite\MD_Converter_Lite.exe'
if (-not (Test-Path -LiteralPath $executable)) {
    throw "the packaged executable was not produced: $executable"
}
Write-Step ("packaged application: {0}" -f $executable)

# ---------------------------------------------------------------------------
# 2. Installer
# ---------------------------------------------------------------------------
$iscc = Get-InnoCompiler
Write-Step ("Inno Setup compiler: {0}" -f $iscc)
Push-Location (Join-Path $RepoRoot 'packaging\windows')
try {
    & $iscc 'MD_Converter.iss'
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}
if (-not (Test-Path -LiteralPath $InstallerOutput)) {
    throw "the installer was not produced: $InstallerOutput"
}

# ---------------------------------------------------------------------------
# 3. Inventory
# ---------------------------------------------------------------------------
$payloadFiles = Get-ChildItem -LiteralPath (Join-Path $RepoRoot 'dist\MD_Converter_Lite') -Recurse -File
$payloadSize = ($payloadFiles | Measure-Object Length -Sum).Sum

Write-Host ''
Write-Host 'RELEASE ARTIFACT INVENTORY'
Write-Host ("  built at            : {0}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'))
Write-Host ("  executable          : {0}" -f $executable)
Write-Host ("  executable bytes    : {0}" -f (Get-Item -LiteralPath $executable).Length)
Write-Host ("  executable sha256   : {0}" -f (Get-FileHash -LiteralPath $executable -Algorithm SHA256).Hash)
Write-Host ("  payload files       : {0}" -f $payloadFiles.Count)
Write-Host ("  payload MB          : {0:N1}" -f ($payloadSize / 1MB))
Write-Host ("  installer           : {0}" -f $InstallerOutput)
Write-Host ("  installer bytes     : {0}" -f (Get-Item -LiteralPath $InstallerOutput).Length)
Write-Host ("  installer sha256    : {0}" -f (Get-FileHash -LiteralPath $InstallerOutput -Algorithm SHA256).Hash)
