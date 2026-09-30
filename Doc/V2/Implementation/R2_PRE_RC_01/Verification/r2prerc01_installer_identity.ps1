#requires -Version 5.1
<#
.SYNOPSIS
    Record the final installer identity and prove the build changed nothing
    else (R2-PRE-RC-01 / WP-02).

.DESCRIPTION
    Verification-only helper. It reads the freshly built Inno Setup installer
    and records its identity, then re-checks the invariants the build must not
    have broken:

      * the accepted packaged payload executable is byte-identical;
      * the frozen Golden baseline artifact is byte-identical;
      * no tracked product runtime source under md_converter/ was modified.

    It never builds, installs, or modifies anything.

.EXAMPLE
    powershell -File Doc/V2/Implementation/R2_PRE_RC_01/Verification/r2prerc01_installer_identity.ps1
#>
[CmdletBinding()]
param(
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
$Installer = Join-Path $RepoRoot 'dist_installer\MD_Converter_v1.1.0_Setup.exe'
$PayloadExe = Join-Path $RepoRoot 'dist\MD_Converter_Lite\MD_Converter_Lite.exe'
$GoldenBaseline = Join-Path $RepoRoot 'md_converter\tests\golden\sample.expected.json'

if (-not $OutputPath) {
    $OutputPath = Join-Path $RepoRoot 'Doc\V2\Implementation\R2_PRE_RC_01\Evidence\WP-R2PRERC01-02_INSTALLER_IDENTITY.json'
}

function Get-Sha256 {
    param([string]$LiteralPath)
    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash
}

foreach ($required in @($Installer, $PayloadExe, $GoldenBaseline)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "missing required input: $required" }
}

$installerItem = Get-Item -LiteralPath $Installer
$installerVersion = $installerItem.VersionInfo

# Expected identity frozen by WP-01 (must survive the build untouched).
$expectedPayloadExe = '68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021'
$expectedGolden = '6D589013B8024C158DE5D29B93BDFEF68F2F406045C805DAB61F8E513725829A'

$payloadExeHash = Get-Sha256 -LiteralPath $PayloadExe
$goldenHash = Get-Sha256 -LiteralPath $GoldenBaseline

# Git-visible product runtime source drift, computed without touching the index.
$productDiff = @(& git -C $RepoRoot diff --numstat -- md_converter) | Where-Object { $_ -match '\S' }
$productDriftFiles = @()
foreach ($line in $productDiff) {
    $parts = ($line -split "`t")
    if ($parts.Count -ge 3) { $productDriftFiles += $parts[2] }
}

$checks = [ordered]@{
    installer_exists          = (Test-Path -LiteralPath $Installer)
    payload_exe_unchanged     = ($payloadExeHash -eq $expectedPayloadExe)
    golden_baseline_unchanged = ($goldenHash -eq $expectedGolden)
    product_runtime_source_files_modified = $productDriftFiles
}

$allPass = $checks.installer_exists -and $checks.payload_exe_unchanged -and $checks.golden_baseline_unchanged

$result = [ordered]@{
    phase                       = 'WP-R2PRERC01-02'
    captured_at                 = (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz')
    installer_filename          = $installerItem.Name
    installer_path              = $installerItem.FullName
    installer_bytes             = $installerItem.Length
    installer_sha256            = (Get-Sha256 -LiteralPath $Installer)
    installer_built_at          = $installerItem.LastWriteTime.ToString('yyyy-MM-ddTHH:mm:sszzz')
    installer_version_info      = [ordered]@{
        file_version    = $installerVersion.FileVersion
        product_version = $installerVersion.ProductVersion
        product_name    = $installerVersion.ProductName
        company_name    = $installerVersion.CompanyName
        file_description = $installerVersion.FileDescription
        legal_copyright = $installerVersion.LegalCopyright
    }
    compiler                    = [ordered]@{
        name    = 'Inno Setup Command-Line Compiler (ISCC.exe)'
        version = 'Inno Setup 7.1.0'
        path    = 'C:\Users\Quansheng\AppData\Local\Programs\Inno Setup 7\ISCC.exe'
    }
    packaged_executable_sha256  = $payloadExeHash
    golden_baseline_path        = $GoldenBaseline
    golden_baseline_sha256      = $goldenHash
    checks                      = $checks
    result                      = if ($allPass) { 'PASS' } else { 'FAIL' }
}

$directory = Split-Path -Parent $OutputPath
if (-not (Test-Path -LiteralPath $directory)) {
    New-Item -ItemType Directory -Path $directory -Force | Out-Null
}
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Host ("installer identity written to {0}" -f $OutputPath)
Write-Host ("  installer sha256 : {0}" -f $result.installer_sha256)
Write-Host ("  payload unchanged: {0}" -f $checks.payload_exe_unchanged)
Write-Host ("  golden unchanged : {0}" -f $checks.golden_baseline_unchanged)
Write-Host ("  result           : {0}" -f $result.result)
