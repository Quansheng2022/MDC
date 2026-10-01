#requires -Version 5.1
<#
.SYNOPSIS
    R2-PRE-RC-02 delta installer lifecycle verification (WP-R2PRERC02-01).

.DESCRIPTION
    Verifies only the distribution risk introduced by HA-02:

        clean uninstall -> install the accepted post-HA02 installer
        -> installed asset/notice inspection -> installed GUI Mermaid + control
        -> uninstall -> reinstall -> short Mermaid smoke

    Verification only.  It never imports the product source, never rebuilds an
    artifact, and never modifies the accepted HA-02 payload or installer.

.EXAMPLE
    powershell -File Doc/V2/Implementation/R2_PRE_RC_02/Verification/r2prerc02_delta_lifecycle.ps1
#>
[CmdletBinding()]
param(
    [string]$InstallerPath,
    [string]$FixturePath,
    [string]$ControlPath,
    [string]$SmokePath,
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
if (-not $SmokePath) {
    $SmokePath = Join-Path $PSScriptRoot 'fixtures\case_a_smoke.md'
}
if (-not $WorkRoot) {
    $WorkRoot = Join-Path $RepoRoot 'build\r2prerc02'
}
if (-not $EvidenceDir) {
    $EvidenceDir = Join-Path $WorkRoot 'evidence'
}

$InstallRoot = Join-Path $env:LOCALAPPDATA 'Programs\MD_Converter'
$InstalledExe = Join-Path $InstallRoot 'MD_Converter.exe'
$Uninstaller = Join-Path $InstallRoot 'unins000.exe'
$InstalledNotice = Join-Path $InstallRoot 'THIRD_PARTY_NOTICES.txt'
$InstalledEula = Join-Path $InstallRoot 'EULA.txt'
$InstalledInternal = Join-Path $InstallRoot '_internal'
$InstalledNode = Join-Path $InstallRoot '_internal\playwright\driver\node.exe'
$InstalledMermaid = Join-Path $InstallRoot '_internal\md_converter\renderer\assets\mermaid.min.js'

$UserWorkspace = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'MD_Converter'
$UserInput = Join-Path $UserWorkspace 'input'
$UserOutput = Join-Path $UserWorkspace 'output'

$Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
$DocxCheck = Join-Path $RepoRoot 'Doc\V2\Implementation\HA_02\Verification\ha02_docx_check.py'
$GuiSmoke = Join-Path $RepoRoot 'tools\packaging\windows_gui_smoke.ps1'

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
    Start-Sleep -Seconds 1
}

function Wait-ForRemoval {
    param([string]$LiteralPath, [int]$TimeoutSeconds = 90)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Test-Path -LiteralPath $LiteralPath) -and ((Get-Date) -lt $deadline)) {
        Start-Sleep -Milliseconds 500
    }
    return -not (Test-Path -LiteralPath $LiteralPath)
}

function Get-WorkspaceSnapshot {
    $snapshot = @{}
    foreach ($directory in @($UserInput, $UserOutput)) {
        if (-not (Test-Path -LiteralPath $directory)) { continue }
        foreach ($file in @(Get-ChildItem -LiteralPath $directory -Recurse -File -ErrorAction SilentlyContinue)) {
            $relative = $file.FullName.Substring($UserWorkspace.Length).TrimStart('\')
            $snapshot[$relative] = (Get-Sha256 -LiteralPath $file.FullName)
        }
    }
    return $snapshot
}

function Compare-WorkspaceSnapshot {
    param([hashtable]$Before, [hashtable]$After)
    $missing = @(); $changed = @(); $added = @()
    foreach ($key in $Before.Keys) {
        if (-not $After.ContainsKey($key)) { $missing += $key }
        elseif ($After[$key] -ne $Before[$key]) { $changed += $key }
    }
    foreach ($key in $After.Keys) {
        if (-not $Before.ContainsKey($key)) { $added += $key }
    }
    return [ordered]@{
        missing = @($missing)
        changed = @($changed)
        added   = @($added)
        intact  = (($missing.Count + $changed.Count) -eq 0)
    }
}

function Invoke-GuiConversion {
    param([string]$Name, [string]$Markdown)
    $caseWork = Join-Path $WorkRoot ("gui_{0}" -f $Name)
    $caseEvidence = Join-Path $EvidenceDir ("gui_smoke_{0}.json" -f $Name)
    $outputDir = Join-Path $caseWork 'output'
    if (Test-Path -LiteralPath $outputDir) { Remove-Item -LiteralPath $outputDir -Recurse -Force }
    $stem = [System.IO.Path]::GetFileNameWithoutExtension($Markdown)
    $docx = Join-Path $outputDir ("{0}.docx" -f $stem)

    Write-Host ("[r2prerc02] installed GUI conversion ({0}): {1}" -f $Name, $Markdown)
    & $GuiSmoke -ExePath $InstalledExe -InputMarkdown $Markdown -WorkDir $caseWork `
        -EvidencePath $caseEvidence -StartupTimeoutSeconds 120 -UiTimeoutSeconds 60 `
        -ConversionTimeoutSeconds 600
    $smokeExit = $LASTEXITCODE

    $entry = [ordered]@{
        name            = $Name
        markdown        = $Markdown
        smoke_exit_code = $smokeExit
        smoke_evidence  = $caseEvidence
        docx_path       = $docx
        docx_exists     = (Test-Path -LiteralPath $docx)
    }
    if ($entry.docx_exists) {
        $entry.docx_bytes = (Get-Item -LiteralPath $docx).Length
        $entry.docx_sha256 = (Get-Sha256 -LiteralPath $docx)
        $mediaDir = Join-Path $caseWork 'media'
        $check = & $Python $DocxCheck $docx '--media-dir' $mediaDir '--json' 2>$null
        $parsed = $check | ConvertFrom-Json
        $entry.inline_images = $parsed.inline_images
        $entry.media_backgrounds = @($parsed.media_stats | ForEach-Object { $_.background })
        $entry.fallback_images = @($parsed.fallback_images)
        $entry.rendered_mermaid = [bool]$parsed.rendered_mermaid
        $entry.paragraphs = $parsed.paragraphs
    }
    return $entry
}

$result = [ordered]@{
    phase        = 'WP-R2PRERC02-01'
    captured_at  = (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz')
    install_root = $InstallRoot
    workspace    = $UserWorkspace
}

# ---------------------------------------------------------------------------
# Step 1 — frozen input identities
# ---------------------------------------------------------------------------
Write-Host '[r2prerc02] step 1: frozen input identities'
$result.identities = [ordered]@{
    installer_path          = $InstallerPath
    installer_bytes         = (Get-Item -LiteralPath $InstallerPath).Length
    installer_sha256        = (Get-Sha256 -LiteralPath $InstallerPath)
    packaged_exe_path       = Join-Path $RepoRoot 'dist\MD_Converter_Lite\MD_Converter_Lite.exe'
    packaged_exe_bytes      = (Get-Item -LiteralPath (Join-Path $RepoRoot 'dist\MD_Converter_Lite\MD_Converter_Lite.exe')).Length
    packaged_exe_sha256     = (Get-Sha256 -LiteralPath (Join-Path $RepoRoot 'dist\MD_Converter_Lite\MD_Converter_Lite.exe'))
    notice_path             = Join-Path $RepoRoot 'THIRD_PARTY_NOTICES.txt'
    notice_bytes            = (Get-Item -LiteralPath (Join-Path $RepoRoot 'THIRD_PARTY_NOTICES.txt')).Length
    notice_sha256           = (Get-Sha256 -LiteralPath (Join-Path $RepoRoot 'THIRD_PARTY_NOTICES.txt'))
    fixture_sha256          = (Get-Sha256 -LiteralPath $FixturePath)
    smoke_fixture_sha256    = (Get-Sha256 -LiteralPath $SmokePath)
}

# ---------------------------------------------------------------------------
# Step 2 — workspace snapshot + backup, then clean uninstall
# ---------------------------------------------------------------------------
Write-Host '[r2prerc02] step 2: workspace snapshot and clean uninstall'
$beforeSnapshot = Get-WorkspaceSnapshot
$result.workspace_before = [ordered]@{
    input_exists  = (Test-Path -LiteralPath $UserInput)
    output_exists = (Test-Path -LiteralPath $UserOutput)
    file_count    = $beforeSnapshot.Count
}
$backupDir = Join-Path $WorkRoot 'workspace_backup'
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
foreach ($directory in @($UserInput, $UserOutput)) {
    if (Test-Path -LiteralPath $directory) {
        $name = Split-Path -Leaf $directory
        Copy-Item -LiteralPath $directory -Destination (Join-Path $backupDir $name) -Recurse -Force
    }
}

Stop-InstalledApp
$result.uninstall_1 = [ordered]@{
    uninstaller_path   = $Uninstaller
    uninstaller_exists = (Test-Path -LiteralPath $Uninstaller)
}
if ($result.uninstall_1.uninstaller_exists) {
    $uninstallLog = Join-Path $WorkRoot 'uninstall_1.log'
    $process = Start-Process -FilePath $Uninstaller -ArgumentList @(
        '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', "/LOG=$uninstallLog"
    ) -Wait -PassThru
    $result.uninstall_1.exit_code = $process.ExitCode
}
if (-not $result.uninstall_1.uninstaller_exists) {
    throw "the normal uninstaller is missing: $Uninstaller"
}
$result.uninstall_1.installed_exe_removed = Wait-ForRemoval -LiteralPath $InstalledExe
$result.uninstall_1.internal_removed = Wait-ForRemoval -LiteralPath $InstalledInternal
$result.uninstall_1.notice_removed = -not (Test-Path -LiteralPath $InstalledNotice)
$afterUninstall = Get-WorkspaceSnapshot
$result.uninstall_1.workspace = Compare-WorkspaceSnapshot -Before $beforeSnapshot -After $afterUninstall

# ---------------------------------------------------------------------------
# Step 3 — install the accepted post-HA02 installer
# ---------------------------------------------------------------------------
Write-Host '[r2prerc02] step 3: install accepted post-HA02 installer'
$installLog1 = Join-Path $WorkRoot 'install_1.log'
$setup = Start-Process -FilePath $InstallerPath -ArgumentList @(
    '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-', "/LOG=$installLog1"
) -Wait -PassThru
$result.install_1 = [ordered]@{
    exit_code            = $setup.ExitCode
    install_dir_exists   = (Test-Path -LiteralPath $InstallRoot)
    installed_exe_exists = (Test-Path -LiteralPath $InstalledExe)
}
if ($result.install_1.installed_exe_exists) {
    $result.install_1.installed_exe_sha256 = (Get-Sha256 -LiteralPath $InstalledExe)
    $result.install_1.installed_exe_matches_payload = (
        $result.install_1.installed_exe_sha256 -eq $result.identities.packaged_exe_sha256
    )
}
$result.install_1.playwright_node_present = Test-Path -LiteralPath $InstalledNode
$result.install_1.mermaid_asset_present = Test-Path -LiteralPath $InstalledMermaid
if ($result.install_1.mermaid_asset_present) {
    $result.install_1.mermaid_asset_sha256 = (Get-Sha256 -LiteralPath $InstalledMermaid)
}
$result.install_1.notice_present = Test-Path -LiteralPath $InstalledNotice
if ($result.install_1.notice_present) {
    $result.install_1.notice_bytes = (Get-Item -LiteralPath $InstalledNotice).Length
    $result.install_1.notice_sha256 = (Get-Sha256 -LiteralPath $InstalledNotice)
    $result.install_1.notice_matches_authoritative = (
        $result.install_1.notice_sha256 -eq $result.identities.notice_sha256
    )
}
$result.install_1.eula_present = Test-Path -LiteralPath $InstalledEula

# ---------------------------------------------------------------------------
# Step 4 — targeted installed GUI conversions
# ---------------------------------------------------------------------------
Write-Host '[r2prerc02] step 4: installed GUI Mermaid fixture and control'
$result.fixture_conversion = Invoke-GuiConversion -Name 'fixture' -Markdown $FixturePath
$result.control_conversion = Invoke-GuiConversion -Name 'control' -Markdown $ControlPath

# ---------------------------------------------------------------------------
# Step 5 — reinstall confirmation
# ---------------------------------------------------------------------------
Write-Host '[r2prerc02] step 5: uninstall/reinstall confirmation'
Stop-InstalledApp
$result.uninstall_2 = [ordered]@{ uninstaller_exists = (Test-Path -LiteralPath $Uninstaller) }
if ($result.uninstall_2.uninstaller_exists) {
    $uninstallLog2 = Join-Path $WorkRoot 'uninstall_2.log'
    $process = Start-Process -FilePath $Uninstaller -ArgumentList @(
        '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', "/LOG=$uninstallLog2"
    ) -Wait -PassThru
    $result.uninstall_2.exit_code = $process.ExitCode
}
if (-not $result.uninstall_2.uninstaller_exists) {
    throw "the normal uninstaller is missing before reinstall: $Uninstaller"
}
$result.uninstall_2.installed_exe_removed = Wait-ForRemoval -LiteralPath $InstalledExe
$afterUninstall2 = Get-WorkspaceSnapshot
$result.uninstall_2.workspace = Compare-WorkspaceSnapshot -Before $beforeSnapshot -After $afterUninstall2

$installLog2 = Join-Path $WorkRoot 'install_2.log'
$setup2 = Start-Process -FilePath $InstallerPath -ArgumentList @(
    '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-', "/LOG=$installLog2"
) -Wait -PassThru
$result.reinstall = [ordered]@{
    exit_code            = $setup2.ExitCode
    installed_exe_exists = (Test-Path -LiteralPath $InstalledExe)
}
if ($result.reinstall.installed_exe_exists) {
    $result.reinstall.installed_exe_sha256 = (Get-Sha256 -LiteralPath $InstalledExe)
    $result.reinstall.installed_exe_matches_payload = (
        $result.reinstall.installed_exe_sha256 -eq $result.identities.packaged_exe_sha256
    )
}
$result.reinstall_smoke = Invoke-GuiConversion -Name 'reinstall_smoke' -Markdown $SmokePath

$result.workspace_after = [ordered]@{
    file_count = (Get-WorkspaceSnapshot).Count
    input_exists = (Test-Path -LiteralPath $UserInput)
    output_exists = (Test-Path -LiteralPath $UserOutput)
}

$written = Join-Path $EvidenceDir 'R2PRERC02-01_LIFECYCLE_RESULT.json'
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $written -Encoding UTF8
Write-Host ("[r2prerc02] evidence written to {0}" -f $written)
$result | ConvertTo-Json -Depth 8
