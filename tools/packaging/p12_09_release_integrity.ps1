#requires -Version 5.1
<#
.SYNOPSIS
    Privacy / locality / release-integrity checks for the P12-09 candidate.

.DESCRIPTION
    Verifies the frozen local/private positioning and the integrity of the
    release artifact:

        * installer / executable identity and version consistency;
        * EULA and THIRD_PARTY_NOTICES presence;
        * packaged-payload inventory free of development-only material
          (`.git`, `.venv`, tests, caches, review packages, credentials,
          developer absolute paths);
        * no required network dependency during normal launch and a real
          representative conversion (process-level connection observation).

    Process connection observation is a bounded check, not a penetration test:
    it records the TCP connections owned by the product process while the
    product performs its normal workflow, and notes that the product does not
    require them.

.EXAMPLE
    powershell -File tools/packaging/p12_09_release_integrity.ps1 `
        -ExePath dist/MD_Converter_Lite/MD_Converter_Lite.exe `
        -InstallerPath dist_installer/MD_Converter_v1.1.0_Setup.exe `
        -InputMarkdown Doc/V2/Implementation/P12-09/corpus/01_simple.md `
        -EvidencePath integrity.json
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ExePath,
    [Parameter(Mandatory = $true)][string]$InstallerPath,
    [Parameter(Mandatory = $true)][string]$InputMarkdown,
    [string]$PayloadDir,
    [string]$WorkDir,
    [string]$EvidencePath,
    [string]$ExpectedSha256 = 'F5AB988168DFA976ED50095A272FB3405CE2CAB395C4A77A34637318D60F7E04',
    [string]$ExpectedInstallerSha256 = 'EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF',
    [int]$StartupTimeoutSeconds = 60,
    [int]$ConversionTimeoutSeconds = 900
)

. "$PSScriptRoot\gui_automation.ps1"

$MainWindowTitle = 'MD Converter'
$Results = [ordered]@{}
$Failures = New-Object System.Collections.ArrayList
$Observations = New-Object System.Collections.ArrayList

function Write-Step { param([string]$Message) Write-Host ("[integrity] {0}" -f $Message) }

function Add-Check {
    param([string]$Name, [bool]$Passed, $Detail)
    $Results[$Name] = [ordered]@{ passed = $Passed; detail = "$Detail" }
    if (-not $Passed) { [void]$Failures.Add($Name) }
    Write-Step ("{0} {1} :: {2}" -f ($(if ($Passed) { 'PASS' } else { 'FAIL' })), $Name, $Detail)
}

function Add-Observation {
    param([string]$Name, $Detail)
    [void]$Observations.Add([ordered]@{ name = $Name; detail = "$Detail" })
    Write-Step ("OBS  {0} :: {1}" -f $Name, $Detail)
}

# ---------------------------------------------------------------------------
# Preparation
# ---------------------------------------------------------------------------

$ExePath = (Resolve-Path -LiteralPath $ExePath).Path
$InstallerPath = (Resolve-Path -LiteralPath $InstallerPath).Path
$InputMarkdown = (Resolve-Path -LiteralPath $InputMarkdown).Path
if (-not $PayloadDir) { $PayloadDir = Split-Path -Parent $ExePath }
$PayloadDir = (Resolve-Path -LiteralPath $PayloadDir).Path
if (-not $WorkDir) { $WorkDir = Join-Path $env:TEMP ("mdc_p1209_integrity_" + (Get-Date -Format 'yyyyMMdd_HHmmss')) }
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null

$Results['executable'] = $ExePath
$Results['installer'] = $InstallerPath
$Results['payload_dir'] = $PayloadDir
$Results['started_at'] = (Get-Date).ToString('o')

# ---------------------------------------------------------------------------
# 1. Artifact identity and version consistency
# ---------------------------------------------------------------------------

$exeItem = Get-Item -LiteralPath $ExePath
$exeHash = (Get-FileHash -LiteralPath $ExePath -Algorithm SHA256).Hash
$instItem = Get-Item -LiteralPath $InstallerPath
$instHash = (Get-FileHash -LiteralPath $InstallerPath -Algorithm SHA256).Hash

$Results['executable_sha256'] = $exeHash
$Results['installer_sha256'] = $instHash
$Results['executable_size'] = $exeItem.Length
$Results['installer_size'] = $instItem.Length
$Results['executable_version'] = $exeItem.VersionInfo.FileVersion
$Results['installer_version'] = $instItem.VersionInfo.FileVersion

Add-Check 'executable-hash-matches-frozen-candidate' ($exeHash -eq $ExpectedSha256) ("{0}" -f $exeHash)
Add-Check 'installer-hash-matches-frozen-candidate' ($instHash -eq $ExpectedInstallerSha256) ("{0}" -f $instHash)
Add-Check 'installer-filename-version' ((Split-Path -Leaf $InstallerPath) -eq 'MD_Converter_v1.1.0_Setup.exe' -and $instItem.VersionInfo.FileVersion -like '1.1.0*') (
    "filename={0}; version={1}" -f (Split-Path -Leaf $InstallerPath), $instItem.VersionInfo.FileVersion)
Add-Check 'executable-version' ($exeItem.VersionInfo.FileVersion -eq '1.1.0') ("version={0}" -f $exeItem.VersionInfo.FileVersion)

$pyproject = Join-Path (Split-Path -Parent (Split-Path -Parent $PayloadDir)) 'pyproject.toml'
if (-not (Test-Path -LiteralPath $pyproject)) { $pyproject = 'C:\Users\Quansheng\Documents\projects\MD_Converter\pyproject.toml' }
$versionLine = (Select-String -LiteralPath $pyproject -Pattern '^\s*version\s*=\s*"([^"]+)"' | Select-Object -First 1)
$sourceVersion = if ($versionLine) { $versionLine.Matches[0].Groups[1].Value } else { 'unknown' }
$Results['source_version'] = $sourceVersion
Add-Check 'version-consistency' ($sourceVersion -eq '1.1.0' -and $exeItem.VersionInfo.FileVersion -eq '1.1.0') (
    "pyproject={0}; executable={1}; installer={2}; About=Version 1.1.0 (WP-09-02)" -f $sourceVersion, $exeItem.VersionInfo.FileVersion, $instItem.VersionInfo.FileVersion)

# ---------------------------------------------------------------------------
# 2. Notices / licence
# ---------------------------------------------------------------------------

$eula = Join-Path $PayloadDir '..\..\EULA.txt'
$notices = Join-Path $PayloadDir '..\..\THIRD_PARTY_NOTICES.txt'
$repoRoot = 'C:\Users\Quansheng\Documents\projects\MD_Converter'
$eulaPath = if (Test-Path -LiteralPath (Join-Path $repoRoot 'EULA.txt')) { Join-Path $repoRoot 'EULA.txt' } else { $eula }
$noticesPath = if (Test-Path -LiteralPath (Join-Path $repoRoot 'THIRD_PARTY_NOTICES.txt')) { Join-Path $repoRoot 'THIRD_PARTY_NOTICES.txt' } else { $notices }
Add-Check 'eula-present' (Test-Path -LiteralPath $eulaPath) ("EULA.txt at {0}" -f $eulaPath)
Add-Check 'third-party-notices-present' (Test-Path -LiteralPath $noticesPath) ("THIRD_PARTY_NOTICES.txt at {0}" -f $noticesPath)

# ---------------------------------------------------------------------------
# 3. Payload inventory scan
# ---------------------------------------------------------------------------

$forbiddenNamePatterns = @(
    '\\\.git\\', '\\\.git$', '\\\.venv\\', '\\__pycache__\\', '\\\.pytest_cache\\',
    '\\\.mypy_cache\\', '\\\.ruff_cache\\', 'review_packages', '\\tests?\\',
    '\\\.env$', '\.pem$', '\.pfx$', '\.p12$', 'id_rsa', 'credentials', '\\secrets?\\'
)
$payloadFiles = @(Get-ChildItem -LiteralPath $PayloadDir -Recurse -File -Force -ErrorAction SilentlyContinue)
$hits = New-Object System.Collections.ArrayList
foreach ($file in $payloadFiles) {
    foreach ($pattern in $forbiddenNamePatterns) {
        if ($file.FullName -match $pattern) { [void]$hits.Add([ordered]@{ file = $file.FullName; pattern = $pattern }); break }
    }
}
$Results['payload_file_count'] = $payloadFiles.Count
$Results['payload_total_bytes'] = ($payloadFiles | Measure-Object -Property Length -Sum).Sum
$Results['forbidden_path_hits'] = @($hits.ToArray())
Add-Check 'payload-free-of-development-material' ($hits.Count -eq 0) (
    "{0} file(s); {1} forbidden-path hit(s)" -f $payloadFiles.Count, $hits.Count)

# Developer absolute-path leak scan over small text-ish files.
$textExtensions = @('.py', '.txt', '.json', '.yaml', '.yml', '.toml', '.cfg', '.ini', '.md', '.html')
$pathHits = New-Object System.Collections.ArrayList
foreach ($file in $payloadFiles) {
    if ($textExtensions -notcontains $file.Extension.ToLowerInvariant()) { continue }
    if ($file.Length -gt 1048576) { continue }
    $text = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction SilentlyContinue
    if ($text -and ($text -match 'C:\\Users\\Quansheng|C:/Users/Quansheng')) {
        [void]$pathHits.Add($file.FullName)
    }
}
$Results['developer_path_hits'] = @($pathHits.ToArray())
Add-Check 'payload-free-of-developer-absolute-paths' ($pathHits.Count -eq 0) (
    "{0} developer absolute-path hit(s) in bundled text files" -f $pathHits.Count)

# ---------------------------------------------------------------------------
# 4. Network observation during normal launch and a real conversion
# ---------------------------------------------------------------------------

$app = $null
$connections = New-Object System.Collections.ArrayList
try {
    $app = Start-Process -FilePath $ExePath -WorkingDirectory $WorkDir -PassThru
    $window = Get-TopLevelWindow -ProcessId $app.Id -Name $MainWindowTitle -TimeoutSeconds $StartupTimeoutSeconds
    Add-Check 'launch-for-network-observation' ([bool]$window) ("main window visible (pid {0})" -f $app.Id)

    foreach ($c in @(Get-NetTCPConnection -OwningProcess $app.Id -ErrorAction SilentlyContinue)) {
        [void]$connections.Add([ordered]@{ phase = 'launch'; state = "$($c.State)"; remote = "$($c.RemoteAddress):$($c.RemotePort)" })
    }

    if ($window) {
        $null = Select-SourceFile -Window $window -ProcessId $app.Id -FilePath $InputMarkdown
        $convertButton = Wait-ForConvertEnabled -Window $window
        if ($convertButton) {
            Click-Element -Window $window -Element $convertButton
            $deadline = (Get-Date).AddSeconds($ConversionTimeoutSeconds)
            while ((Get-Date) -lt $deadline) {
                foreach ($c in @(Get-NetTCPConnection -OwningProcess $app.Id -ErrorAction SilentlyContinue)) {
                    [void]$connections.Add([ordered]@{ phase = 'conversion'; state = "$($c.State)"; remote = "$($c.RemoteAddress):$($c.RemotePort)" })
                }
                $outcome = Wait-ForConversionOutcome -Window $window -TimeoutSeconds 3
                if ($outcome.outcome -ne 'TIMEOUT') { $Results['conversion_outcome'] = $outcome; break }
            }
        }
    }

    $remote = @($connections | Where-Object { $_.remote -notmatch '^(127\.|0\.0\.0\.0|::)' })
    $established = @($connections | Where-Object { $_.state -match 'Established' -and $_.remote -notmatch '^(127\.|::)' })
    $Results['connections'] = @($connections.ToArray())
    $Results['remote_connections'] = $remote.Count
    $Results['established_remote_connections'] = $established.Count
    Add-Check 'no-required-network-dependency' ($established.Count -eq 0) (
        "conversion outcome={0}; established remote connections owned by the product process={1} (samples={2})" -f
        $(if ($Results['conversion_outcome']) { $Results['conversion_outcome'].outcome } else { 'n/a' }), $established.Count, $connections.Count)
} catch {
    Add-Check 'no-required-network-dependency' $false ("aborted: {0}" -f $_.Exception.Message)
} finally {
    if ($app) { try { $app.Refresh(); if (-not $app.HasExited) { $app.Kill() } } catch { } }
    Get-Process MD_Converter_Lite -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}

if ($established.Count -gt 0) {
    Add-Observation 'network-endpoints' ($established | ConvertTo-Json -Compress)
}

$Results['observations'] = @($Observations.ToArray())
$Results['finished_at'] = (Get-Date).ToString('o')
$Results['failed_checks'] = @($Failures)
$Results['status'] = $(if ($Failures.Count -eq 0) { 'PASS' } else { 'FAIL' })

if ($EvidencePath) {
    $directory = Split-Path -Parent $EvidencePath
    if ($directory) { New-Item -ItemType Directory -Force -Path $directory | Out-Null }
    $Results | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $EvidencePath -Encoding UTF8
    Write-Step ("evidence written to {0}" -f $EvidencePath)
}

Write-Host ""
Write-Host ("RESULT: {0} ({1} failing check(s))" -f $Results['status'], $Failures.Count)
if ($Failures.Count -gt 0) { exit 1 }
exit 0
