#requires -Version 5.1
<#
.SYNOPSIS
    R2-RC release-critical identity recheck (WP-R2RC-01).

.DESCRIPTION
    Verification-only helper. It recomputes the release-critical identities of the
    accepted R2 candidate and compares them with the values frozen by R2-V02,
    R2-V04 and R2-PRE-RC-01. It never rebuilds the payload or the installer and
    never touches product source.

    The payload tree digest uses the same deterministic algorithm as
    Doc/V2/Implementation/R2_PRE_RC_01/Verification/r2prerc01_payload_identity.ps1:
    SHA-256 over the sorted "<relative path> <size> <sha256>" lines of the tree.

.EXAMPLE
    powershell -File Doc/V2/Implementation/R2_RC/Verification/r2rc_identity_check.ps1
#>
[CmdletBinding()]
param(
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
$PayloadDir = Join-Path $RepoRoot 'dist\MD_Converter_Lite'
$PayloadExe = Join-Path $PayloadDir 'MD_Converter_Lite.exe'
$Installer = Join-Path $RepoRoot 'dist_installer\MD_Converter_v1.1.0_Setup.exe'
$Golden = Join-Path $RepoRoot 'md_converter\tests\golden\sample.expected.json'
$Iss = Join-Path $RepoRoot 'packaging\windows\MD_Converter.iss'

# Values accepted by R2-V02 / R2-V04 / R2-PRE-RC-01.
$Expected = [ordered]@{
    installer_sha256           = '4B56FC989BAB7FF7E648CC29DFE5A6D944B2B8EFC420F11DE8D0ECF8294FFDE9'
    installer_bytes            = 51186717L
    payload_exe_sha256         = '68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021'
    payload_exe_bytes          = 6926650L
    payload_tree_digest_sha256 = 'ecb6a4453f342af51cbc2b26b175489cb4ad963bc987a7407ff10ff0f8efa96c'
    payload_file_count         = 268
    payload_total_bytes        = 166231301L
    golden_baseline_sha256     = '6D589013B8024C158DE5D29B93BDFEF68F2F406045C805DAB61F8E513725829A'
    installer_script_sha256    = 'EBB0979972348ECA2926BC3095049BDB047B36F206E9D66E2A1C7E468B91CE03'
}

function Get-Sha256 {
    param([string]$LiteralPath)
    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash
}

foreach ($required in @($PayloadExe, $Installer, $Golden, $Iss)) {
    if (-not (Test-Path -LiteralPath $required)) {
        throw "release-critical input is missing: $required"
    }
}

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
    $treeDigest = ($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($manifestText)) |
        ForEach-Object { $_.ToString('x2') }) -join ''
}
finally {
    $sha.Dispose()
}

$Actual = [ordered]@{
    installer_sha256           = Get-Sha256 -LiteralPath $Installer
    installer_bytes            = (Get-Item -LiteralPath $Installer).Length
    payload_exe_sha256         = Get-Sha256 -LiteralPath $PayloadExe
    payload_exe_bytes          = (Get-Item -LiteralPath $PayloadExe).Length
    payload_tree_digest_sha256 = $treeDigest
    payload_file_count         = $files.Count
    payload_total_bytes        = $totalBytes
    golden_baseline_sha256     = Get-Sha256 -LiteralPath $Golden
    installer_script_sha256    = Get-Sha256 -LiteralPath $Iss
}

$mismatches = New-Object System.Collections.Generic.List[string]
foreach ($key in $Expected.Keys) {
    if ($Actual[$key] -ne $Expected[$key]) { $mismatches.Add($key) }
}

$result = [ordered]@{
    phase           = 'WP-R2RC-01'
    captured_at     = (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz')
    repository_root = $RepoRoot
    branch          = (& git -C $RepoRoot rev-parse --abbrev-ref HEAD)
    head            = (& git -C $RepoRoot rev-parse HEAD)
    expected        = $Expected
    actual          = $Actual
    mismatches      = @($mismatches)
    result          = $(if ($mismatches.Count -eq 0) { 'PASS' } else { 'ARTIFACT_MISMATCH' })
}

if ($OutputPath) {
    $directory = Split-Path -Parent $OutputPath
    if ($directory -and -not (Test-Path -LiteralPath $directory)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }
    $result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
}

$result | ConvertTo-Json -Depth 6
