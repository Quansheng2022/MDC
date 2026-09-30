#requires -Version 5.1
<#
.SYNOPSIS
    Freeze the accepted R2 packaged-payload identity (R2-PRE-RC-01 / WP-01).

.DESCRIPTION
    Verification-only helper. It never touches product source and never
    rebuilds the payload. It records, for the accepted packaged payload
    (dist\MD_Converter_Lite):

      * the packaged executable size and SHA-256;
      * the executable version resource;
      * the authoritative project version from pyproject.toml;
      * the number of payload files and their total size;
      * a deterministic whole-tree digest over "<relative path> <size> <sha256>".

    Output is written as JSON next to the WP-01 evidence.

.EXAMPLE
    powershell -File Doc/V2/Implementation/R2_PRE_RC_01/Verification/r2prerc01_payload_identity.ps1
#>
[CmdletBinding()]
param(
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
$PayloadDir = Join-Path $RepoRoot 'dist\MD_Converter_Lite'
$PayloadExe = Join-Path $PayloadDir 'MD_Converter_Lite.exe'
$PyProject = Join-Path $RepoRoot 'pyproject.toml'

if (-not $OutputPath) {
    $OutputPath = Join-Path $RepoRoot 'Doc\V2\Implementation\R2_PRE_RC_01\Evidence\WP-R2PRERC01-01_PAYLOAD_IDENTITY.json'
}

if (-not (Test-Path -LiteralPath $PayloadExe)) {
    throw "accepted payload executable is missing: $PayloadExe"
}

function Get-Sha256 {
    param([string]$LiteralPath)
    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash
}

$exeItem = Get-Item -LiteralPath $PayloadExe
$exeHash = Get-Sha256 -LiteralPath $PayloadExe
$versionInfo = $exeItem.VersionInfo

# Authoritative project version (single source: pyproject.toml [project].version).
$projectVersion = $null
$inProjectSection = $false
foreach ($line in Get-Content -LiteralPath $PyProject -Encoding UTF8) {
    if ($line -match '^\s*\[project\]\s*$') { $inProjectSection = $true; continue }
    if ($line -match '^\s*\[.+\]\s*$') { $inProjectSection = $false; continue }
    if ($inProjectSection -and $line -match '^\s*version\s*=\s*"([^"]+)"\s*$') {
        $projectVersion = $Matches[1]
        break
    }
}
if (-not $projectVersion) { throw 'could not resolve [project].version from pyproject.toml' }

# Frozen installer script (Inno Setup) identity.
$issPath = Join-Path $RepoRoot 'packaging\windows\MD_Converter.iss'
$issText = Get-Content -LiteralPath $issPath -Raw -Encoding UTF8
function Get-IssDefine {
    param([string]$Name)
    $pattern = '(?m)^\s*#define\s+' + [regex]::Escape($Name) + '\s+"([^"]*)"'
    $m = [regex]::Match($issText, $pattern)
    if ($m.Success) { return $m.Groups[1].Value }
    return $null
}

# Deterministic payload tree digest (sorted by relative path).
$files = Get-ChildItem -LiteralPath $PayloadDir -Recurse -File | Sort-Object FullName
$lines = New-Object System.Collections.Generic.List[string]
$totalBytes = 0L
foreach ($file in $files) {
    $relative = $file.FullName.Substring($PayloadDir.Length).TrimStart('\') -replace '\\', '/'
    $totalBytes += $file.Length
    $lines.Add(('{0} {1} {2}' -f $relative, $file.Length, (Get-Sha256 -LiteralPath $file.FullName)))
}
$manifestText = ($lines -join "`n") + "`n"
$sha = [System.Security.Cryptography.SHA256]::Create()
try {
    $treeDigest = ($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($manifestText)) | ForEach-Object { $_.ToString('x2') }) -join ''
} finally {
    $sha.Dispose()
}

$result = [ordered]@{
    phase                      = 'WP-R2PRERC01-01'
    captured_at                = (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz')
    repository_root            = $RepoRoot
    payload_directory          = $PayloadDir
    payload_manifest_file      = $PayloadExe
    payload_file_count         = $files.Count
    payload_total_bytes        = $totalBytes
    payload_tree_digest_sha256 = $treeDigest
    payload_exe_bytes          = $exeItem.Length
    payload_exe_sha256         = $exeHash
    exe_version_info           = [ordered]@{
        file_version    = $versionInfo.FileVersion
        product_version = $versionInfo.ProductVersion
        product_name    = $versionInfo.ProductName
        company_name    = $versionInfo.CompanyName
        original_name   = $versionInfo.OriginalFilename
    }
    authoritative_version      = [ordered]@{
        source            = 'pyproject.toml [project].version'
        version           = $projectVersion
        iss_app_id        = (Get-IssDefine 'MyAppId')
        iss_app_name      = (Get-IssDefine 'MyAppName')
        iss_app_version   = (Get-IssDefine 'MyAppVersion')
        iss_app_publisher = (Get-IssDefine 'MyAppPublisher')
    }
    installer_script           = $issPath
    installer_script_sha256    = (Get-Sha256 -LiteralPath $issPath)
}

$directory = Split-Path -Parent $OutputPath
if (-not (Test-Path -LiteralPath $directory)) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
}
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Host ("payload identity written to {0}" -f $OutputPath)
Write-Host ("  payload exe sha256 : {0}" -f $exeHash)
Write-Host ("  payload tree digest: {0}" -f $treeDigest)
Write-Host ("  files / bytes      : {0} / {1}" -f $files.Count, $totalBytes)
