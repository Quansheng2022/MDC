<#
.SYNOPSIS
    R2-V03 native Word / visual verification environment recorder.

.DESCRIPTION
    Verification-only helper. Records the accepted R2-V02 packaged runtime
    identity and the native Microsoft Word / Windows display environment used by
    the R2-V03 gate. Writes one JSON document. Reads only; it never modifies the
    installed product, the repository, or any product setting.

.EXAMPLE
    powershell -NoProfile -File r2v03_env_record.ps1 `
        -InstallExe "$env:LOCALAPPDATA\Programs\MD_Converter\MD_Converter.exe" `
        -PayloadExe "dist\MD_Converter_Lite\MD_Converter_Lite.exe" `
        -Output "Doc\V2\Implementation\R2_V03\Evidence\R2_V03_ENVIRONMENT.json"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$InstallExe,
    [Parameter(Mandatory = $true)][string]$PayloadExe,
    [Parameter(Mandatory = $true)][string]$Output
)

$ErrorActionPreference = 'Stop'

function Get-FileIdentity {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return [ordered]@{ path = $Path; present = $false }
    }
    $item = Get-Item -LiteralPath $Path
    $info = $item.VersionInfo
    return [ordered]@{
        path           = $item.FullName
        present        = $true
        bytes          = $item.Length
        last_write_utc = $item.LastWriteTimeUtc.ToString('o')
        sha256         = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash
        file_version   = $info.FileVersion
        product_version = $info.ProductVersion
        product_name   = $info.ProductName
        company_name   = $info.CompanyName
    }
}

function Get-RegistryValue {
    param([string]$Path, [string]$Name)
    try {
        $value = (Get-ItemProperty -LiteralPath $Path -Name $Name -ErrorAction Stop).$Name
        return $value
    } catch {
        return $null
    }
}

# --- accepted R2-V02 packaged runtime identity -------------------------------
$install = Get-FileIdentity -Path $InstallExe
$payload = Get-FileIdentity -Path $PayloadExe
$identityMatch = $null
if ($install.present -and $payload.present) {
    $identityMatch = ($install.sha256 -eq $payload.sha256)
}

# --- native Microsoft Word ---------------------------------------------------
$wordCandidates = @(
    'C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE',
    'C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE'
)
$wordExe = $wordCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
$word = [ordered]@{ present = $false }
if ($wordExe) {
    $w = Get-Item -LiteralPath $wordExe
    $word = [ordered]@{
        present        = $true
        path           = $w.FullName
        file_version   = $w.VersionInfo.FileVersion
        product_version = $w.VersionInfo.ProductVersion
        product_name   = $w.VersionInfo.ProductName
    }
}
$officeC2R = [ordered]@{
    product_release_ids = Get-RegistryValue 'HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration' 'ProductReleaseIds'
    version_to_report   = Get-RegistryValue 'HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration' 'VersionToReport'
    platform            = Get-RegistryValue 'HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration' 'Platform'
    client_version      = Get-RegistryValue 'HKLM:\SOFTWARE\Microsoft\Office\ClickToRun\Configuration' 'ClientVersionToReport'
}

# --- Windows + display -------------------------------------------------------
$cv = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
$windows = [ordered]@{
    product_name     = Get-RegistryValue $cv 'ProductName'
    display_version  = Get-RegistryValue $cv 'DisplayVersion'
    release_id       = Get-RegistryValue $cv 'ReleaseId'
    current_build    = Get-RegistryValue $cv 'CurrentBuild'
    ubr              = Get-RegistryValue $cv 'UBR'
    os_architecture  = $env:PROCESSOR_ARCHITECTURE
}
$logPixels = Get-RegistryValue 'HKCU:\Control Panel\Desktop' 'LogPixels'
$display = [ordered]@{
    log_pixels        = $logPixels
    scale_percent     = if ($logPixels) { [math]::Round(100.0 * [double]$logPixels / 96.0, 1) } else { $null }
    monitor_dpi_scale = Get-RegistryValue 'HKCU:\Control Panel\Desktop' 'Win8DpiScaling'
}
try {
    Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
    $screens = [System.Windows.Forms.Screen]::AllScreens | ForEach-Object {
        [ordered]@{
            device_name = $_.DeviceName
            primary     = $_.Primary
            bounds      = "$($_.Bounds.Width)x$($_.Bounds.Height)"
            work_area   = "$($_.WorkingArea.Width)x$($_.WorkingArea.Height)"
        }
    }
    $display.screens = @($screens)
} catch {
    $display.screens = @()
}

$record = [ordered]@{
    generated_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    generated_at_local = (Get-Date).ToString('o')
    program          = 'R2-V03'
    note             = 'Verification-only environment/identity record. No product or system state was modified.'
    installed_runtime = $install
    built_payload     = $payload
    installed_matches_built_payload = $identityMatch
    expected_executable_sha256 = '68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021'
    microsoft_word    = $word
    office_click_to_run = $officeC2R
    windows           = $windows
    display           = $display
}

$dir = Split-Path -Parent $Output
if ($dir -and -not (Test-Path -LiteralPath $dir)) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Output -Encoding UTF8
Write-Output "WROTE $Output"
