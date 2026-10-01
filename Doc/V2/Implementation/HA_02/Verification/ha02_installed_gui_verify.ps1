#requires -Version 5.1
<#
.SYNOPSIS
    HA-02 installed-application Mermaid verification (WP-HA02-02).

.DESCRIPTION
    Installs the rebuilt candidate silently, then drives the *installed*
    application through its normal GUI path (Windows UI Automation) to convert
    the unchanged HA-02 fixture, and finally inspects the produced DOCX to prove
    the Mermaid figures are real renders rather than the raw-source fallback.
    A non-Mermaid control document is converted the same way.

    Verification only: it never imports the source tree and performs no
    conversion logic of its own.

.EXAMPLE
    powershell -File Doc/V2/Implementation/HA_02/Verification/ha02_installed_gui_verify.ps1 `
        -FixturePath input_test/mermaid_triangle/test_mermaid_triangle_v2.md `
        -ControlPath md_converter/tests/acceptance/AC001_simple.md
#>
[CmdletBinding()]
param(
    [string]$InstallerPath,
    [string]$FixturePath,
    [string]$ControlPath,
    [string]$WorkRoot,
    [string]$EvidenceDir
)

$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
if (-not $InstallerPath) {
    $InstallerPath = Join-Path $RepoRoot 'dist_installer\MD_Converter_v1.1.0_Setup.exe'
}
if (-not $FixturePath) {
    $FixturePath = Join-Path $RepoRoot 'input_test\mermaid_triangle\test_mermaid_triangle_v2.md'
}
if (-not $ControlPath) {
    $ControlPath = Join-Path $RepoRoot 'md_converter\tests\acceptance\AC001_simple.md'
}
if (-not $WorkRoot) {
    $WorkRoot = Join-Path $RepoRoot 'build\ha02_installed'
}
if (-not $EvidenceDir) {
    $EvidenceDir = Join-Path $WorkRoot 'evidence'
}

$InstallRoot = Join-Path $env:LOCALAPPDATA 'Programs\MD_Converter'
$InstalledExe = Join-Path $InstallRoot 'MD_Converter.exe'

New-Item -ItemType Directory -Force -Path $WorkRoot, $EvidenceDir | Out-Null

function Get-Sha256 {
    param([string]$LiteralPath)
    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash
}

function Stop-InstalledApp {
    foreach ($process in @(Get-Process -Name 'MD_Converter' -ErrorAction SilentlyContinue)) {
        try { $process.CloseMainWindow() | Out-Null } catch { }
    }
    Start-Sleep -Seconds 2
    foreach ($process in @(Get-Process -Name 'MD_Converter' -ErrorAction SilentlyContinue)) {
        try { $process.Kill() } catch { }
    }
}

$result = [ordered]@{
    phase               = 'WP-HA02-02'
    captured_at         = (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz')
    installer_path      = $InstallerPath
    installer_bytes     = (Get-Item -LiteralPath $InstallerPath).Length
    installer_sha256    = (Get-Sha256 -LiteralPath $InstallerPath)
    install_root        = $InstallRoot
    cases               = @()
}

Write-Host '[ha02] stopping any running installed application'
Stop-InstalledApp

$installLog = Join-Path $WorkRoot 'install.log'
Write-Host '[ha02] silent install of the rebuilt candidate'
$setup = Start-Process -FilePath $InstallerPath -ArgumentList @(
    '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-', "/LOG=$installLog"
) -Wait -PassThru
$result.install_exit_code = $setup.ExitCode

if (-not (Test-Path -LiteralPath $InstalledExe)) {
    throw "installed executable missing after setup: $InstalledExe"
}
$result.installed_exe_path = $InstalledExe
$result.installed_exe_bytes = (Get-Item -LiteralPath $InstalledExe).Length
$result.installed_exe_sha256 = (Get-Sha256 -LiteralPath $InstalledExe)
$result.playwright_in_install = Test-Path -LiteralPath (Join-Path $InstallRoot '_internal\playwright\driver\node.exe')
$result.mermaid_asset_in_install = Test-Path -LiteralPath (
    Join-Path $InstallRoot '_internal\md_converter\renderer\assets\mermaid.min.js'
)

foreach ($case in @(
        @{ name = 'fixture'; file = $FixturePath },
        @{ name = 'control'; file = $ControlPath }
    )) {
    $caseName = $case.name
    $markdown = $case.file
    $caseWork = Join-Path $WorkRoot ("gui_{0}" -f $caseName)
    $caseEvidence = Join-Path $EvidenceDir ("gui_smoke_{0}.json" -f $caseName)
    $outputDir = Join-Path $caseWork 'output'
    $stem = [System.IO.Path]::GetFileNameWithoutExtension($markdown)
    $docx = Join-Path $outputDir ("{0}.docx" -f $stem)

    if (Test-Path -LiteralPath $outputDir) {
        Remove-Item -LiteralPath $outputDir -Recurse -Force
    }

    Write-Host ("[ha02] GUI conversion ({0}): {1}" -f $caseName, $markdown)
    & (Join-Path $RepoRoot 'tools\packaging\windows_gui_smoke.ps1') `
        -ExePath $InstalledExe `
        -InputMarkdown $markdown `
        -WorkDir $caseWork `
        -EvidencePath $caseEvidence `
        -StartupTimeoutSeconds 120 `
        -UiTimeoutSeconds 60 `
        -ConversionTimeoutSeconds 900
    $smokeExit = $LASTEXITCODE

    $entry = [ordered]@{
        case            = $caseName
        markdown        = $markdown
        markdown_sha256 = (Get-Sha256 -LiteralPath $markdown)
        work_dir        = $caseWork
        smoke_exit_code = $smokeExit
        smoke_evidence  = $caseEvidence
        docx_path       = $docx
        docx_exists     = (Test-Path -LiteralPath $docx)
    }
    if ($entry.docx_exists) {
        $entry.docx_bytes = (Get-Item -LiteralPath $docx).Length
        $entry.docx_sha256 = (Get-Sha256 -LiteralPath $docx)
        $check = & (Join-Path $RepoRoot '.venv\Scripts\python.exe') `
            (Join-Path $RepoRoot 'Doc\V2\Implementation\HA_02\Verification\ha02_docx_check.py') `
            $docx '--json'
        $parsed = $check | ConvertFrom-Json
        $entry.inline_images = $parsed.inline_images
        $entry.media_backgrounds = @($parsed.media_stats | ForEach-Object { $_.background })
        $entry.fallback_images = @($parsed.fallback_images)
        $entry.rendered_mermaid = [bool]$parsed.rendered_mermaid
    }
    $result.cases += $entry
}

Stop-InstalledApp

$written = Join-Path $EvidenceDir 'WP-HA02-02_INSTALLED_RESULT.json'
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $written -Encoding UTF8
Write-Host ("[ha02] evidence written to {0}" -f $written)
$result | ConvertTo-Json -Depth 8
