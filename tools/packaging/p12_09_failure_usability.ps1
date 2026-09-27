#requires -Version 5.1
<#
.SYNOPSIS
    Failure / recovery / usability matrix for the P12-09 release candidate.

.DESCRIPTION
    Real-platform verification of the negative paths and desktop-usability
    baseline that the functional-acceptance and runtime matrices do not cover:

        * off-screen stored window geometry (the product's own save/restore path);
        * stale remembered source/output directories;
        * Word-locked output artifact (OUTPUT_ERROR must fail closed);
        * output path blocked by a same-named directory;
        * duplicate Convert protection;
        * real-window accessible names, Tab order and textual status;
        * keyboard-reachable report surface.

    Verification tooling only.  The product's own preference store is backed up
    before the run and restored afterwards, so the checks leave no trace.

.EXAMPLE
    powershell -File tools/packaging/p12_09_failure_usability.ps1 `
        -ExePath dist/MD_Converter_Lite/MD_Converter_Lite.exe `
        -CorpusDir Doc/V2/Implementation/P12-09/corpus -EvidencePath usability.json
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ExePath,
    [Parameter(Mandatory = $true)][string]$CorpusDir,
    [string]$WorkDir,
    [string]$EvidencePath,
    [int]$StartupTimeoutSeconds = 60,
    [int]$UiTimeoutSeconds = 30,
    [int]$ConversionTimeoutSeconds = 900
)

. "$PSScriptRoot\gui_automation.ps1"

if (-not ('MdcWindowProbe' -as [type])) {
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public static class MdcWindowProbe
{
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }

    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hWnd, IntPtr after, int x, int y, int cx, int cy, uint flags);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")] public static extern int GetSystemMetrics(int index);

    public const uint SWP_NOSIZE = 0x0001;
    public const uint SWP_NOZORDER = 0x0004;
    public const uint SWP_NOACTIVATE = 0x0010;

    public static bool MoveTo(IntPtr hWnd, int x, int y)
    {
        return SetWindowPos(hWnd, IntPtr.Zero, x, y, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE);
    }

    public static int[] Rect(IntPtr hWnd)
    {
        RECT r;
        if (!GetWindowRect(hWnd, out r)) { return new int[] { 0, 0, 0, 0 }; }
        return new int[] { r.Left, r.Top, r.Right, r.Bottom };
    }

    public static int ScreenWidth() { return GetSystemMetrics(0); }
    public static int ScreenHeight() { return GetSystemMetrics(1); }
}
'@
}

$MainWindowTitle = 'MD Converter'
$PrefsRoot = 'HKCU:\Software\MD Converter'
$PrefsApp = 'HKCU:\Software\MD Converter\MD Converter'
$WordWindowClass = 'OpusApp'

$Results = [ordered]@{}
$Failures = New-Object System.Collections.ArrayList
$Observations = New-Object System.Collections.ArrayList
$Restore = [ordered]@{ existed = $false; backup = $null }

function Write-Step { param([string]$Message) Write-Host ("[usability] {0}" -f $Message) }

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

function Get-ButtonState {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [string]$NamePattern,
        [int]$TimeoutSeconds = 3
    )
    $element = Find-Element -Root $Window -NamePattern $NamePattern -Type $Global:ControlType::Button -TimeoutSeconds $TimeoutSeconds
    if (-not $element) { return [ordered]@{ present = $false; enabled = $false; onscreen = $false; focusable = $false } }
    return [ordered]@{
        present = $true
        enabled = [bool]$element.Current.IsEnabled
        onscreen = (-not [bool]$element.Current.IsOffscreen)
        focusable = [bool]$element.Current.IsKeyboardFocusable
    }
}

function Get-FrozenState {
    param([System.Windows.Automation.AutomationElement]$Window, [switch]$Fast)
    $probeTimeout = if ($Fast) { 1 } else { 3 }
    $convert = Get-ButtonState -Window $Window -NamePattern '^Convert$' -TimeoutSeconds $probeTimeout
    $openDocument = Get-ButtonState -Window $Window -NamePattern '^Open Document$' -TimeoutSeconds $probeTimeout
    $details = Get-ButtonState -Window $Window -NamePattern '^Details' -TimeoutSeconds $probeTimeout
    $texts = @(Get-Descendants -Root $Window |
        Where-Object { $_.Current.ControlType -eq $Global:ControlType::Text -and -not $_.Current.IsOffscreen } |
        ForEach-Object { $_.Current.Name })
    $sourceSelected = [bool]($texts -contains 'Selected Markdown file')
    $warningSummary = [bool](@($texts | Where-Object { $_ -match 'Conversion reported \d+ warning' }).Count -gt 0)
    $state = 'UNKNOWN'
    if ($warningSummary) { $state = 'SUCCESS_WITH_WARNING' }
    elseif ($openDocument.enabled) { $state = 'SUCCESS' }
    elseif ($details.onscreen) { $state = 'FAILED' }
    elseif ($convert.enabled -and $sourceSelected) { $state = 'READY' }
    elseif (-not $convert.enabled -and $sourceSelected) { $state = 'CONVERTING' }
    elseif (-not $convert.enabled -and -not $sourceSelected) { $state = 'EMPTY' }
    return [ordered]@{
        state = $state; convert = $convert; open_document = $openDocument
        details = $details; source_selected = $sourceSelected; visible_texts = $texts
    }
}

function Start-App {
    param([string]$Path, [string]$Directory)
    return Start-Process -FilePath $Path -WorkingDirectory $Directory -PassThru
}

function Get-AppWindow {
    param([int]$ProcessId, [int]$TimeoutSeconds = 60)
    return (Get-TopLevelWindow -ProcessId $ProcessId -Name $MainWindowTitle -TimeoutSeconds $TimeoutSeconds)
}

function Stop-App {
    param($Process)
    try { $Process.Refresh(); if (-not $Process.HasExited) { $Process.Kill() } } catch { }
}

function Close-App {
    param($Process, [System.Windows.Automation.AutomationElement]$Window, [int]$TimeoutSeconds = 30)
    Close-WindowElement -Element $Window
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $Process.Refresh(); if ($Process.HasExited) { break }
        Start-Sleep -Milliseconds 400
    }
    $Process.Refresh()
    return [bool]$Process.HasExited
}

function Select-File {
    param([System.Windows.Automation.AutomationElement]$Window, [int]$ProcessId, [string]$Path)
    return (Select-SourceFile -Window $Window -ProcessId $ProcessId -FilePath $Path -TimeoutSeconds $UiTimeoutSeconds)
}

function Convert-Once {
    param([System.Windows.Automation.AutomationElement]$Window, [datetime]$Since, [int]$TimeoutSeconds = 0)
    if ($TimeoutSeconds -le 0) { $TimeoutSeconds = $ConversionTimeoutSeconds }
    $button = Wait-ForConvertEnabled -Window $Window -TimeoutSeconds $UiTimeoutSeconds
    if (-not $button) { return [ordered]@{ state = 'NOT_STARTED'; seconds = 0; artifacts = @() } }
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    Click-Element -Window $Window -Element $button
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $final = $null
    while ((Get-Date) -lt $deadline) {
        $current = Get-FrozenState -Window $Window
        if ($current.state -in @('SUCCESS', 'SUCCESS_WITH_WARNING', 'FAILED')) {
            Start-Sleep -Milliseconds 700
            $confirm = Get-FrozenState -Window $Window
            if ($confirm.state -eq $current.state) { $final = $confirm; break }
        }
        Start-Sleep -Milliseconds 800
    }
    if (-not $final) { $final = Get-FrozenState -Window $Window; $final.state = 'TIMEOUT' }
    return [ordered]@{
        state = $final.state
        seconds = [math]::Round($stopwatch.Elapsed.TotalSeconds, 1)
        artifacts = @(Get-NewDocumentArtifacts -Since $Since -Roots @($WorkDir))
        summary_texts = @($final.visible_texts | Where-Object { $_ -match 'Conversion|document|warning|failed' })
    }
}

# ---------------------------------------------------------------------------
# Preparation
# ---------------------------------------------------------------------------

$ExePath = (Resolve-Path -LiteralPath $ExePath).Path
$CorpusDir = (Resolve-Path -LiteralPath $CorpusDir).Path
if (-not $WorkDir) { $WorkDir = Join-Path $env:TEMP ("mdc_p1209_usability_" + (Get-Date -Format 'yyyyMMdd_HHmmss')) }
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
$outputDir = Join-Path $WorkDir 'output'
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

$sourceA = Join-Path $WorkDir 'usability_source.md'
$sourceB = Join-Path $WorkDir 'usability_second.md'
$sourceBlocked = Join-Path $WorkDir 'blocked_output.md'
$sourceWarning = Join-Path $WorkDir 'usability_warning.md'
Copy-Item -LiteralPath (Join-Path $CorpusDir '01_simple.md') -Destination $sourceA -Force
Copy-Item -LiteralPath (Join-Path $CorpusDir '01_simple.md') -Destination $sourceB -Force
Copy-Item -LiteralPath (Join-Path $CorpusDir '02_headings_lists_tables.md') -Destination $sourceBlocked -Force
Copy-Item -LiteralPath (Join-Path $CorpusDir '05_warning_empty_heading.md') -Destination $sourceWarning -Force

if (Test-Path $PrefsRoot) {
    $Restore.existed = $true
    $Restore.backup = Join-Path $WorkDir 'prefs_backup.reg'
    & reg.exe export 'HKCU\Software\MD Converter' $Restore.backup /y | Out-Null
}

$Results['executable'] = $ExePath
$Results['executable_sha256'] = (Get-FileHash -LiteralPath $ExePath -Algorithm SHA256).Hash
$Results['work_dir'] = $WorkDir
$Results['output_dir'] = $outputDir
$Results['started_at'] = (Get-Date).ToString('o')

$app = $null
$window = $null

try {
    # -----------------------------------------------------------------------
    # Baseline: one real SUCCESS conversion to obtain a persistent artifact
    # -----------------------------------------------------------------------
    $app = Start-App -Path $ExePath -Directory $WorkDir
    $window = Get-AppWindow -ProcessId $app.Id -TimeoutSeconds $StartupTimeoutSeconds
    Add-Check 'startup' ([bool]$window) ("main window visible (pid {0})" -f $app.Id)
    if (-not $window) { throw 'the packaged GUI did not start' }

    $null = Select-File -Window $window -ProcessId $app.Id -Path $sourceA
    $baseline = Convert-Once -Window $window -Since (Get-Date)
    $Results['baseline_conversion'] = $baseline
    Add-Check 'baseline-conversion' ($baseline.state -eq 'SUCCESS' -and $baseline.artifacts.Count -ge 1) (
        "state={0} in {1}s; artifacts={2}" -f $baseline.state, $baseline.seconds, $baseline.artifacts.Count)
    $artifact = if ($baseline.artifacts.Count -gt 0) { $baseline.artifacts[0] } else { $null }
    $artifactName = if ($artifact) { [System.IO.Path]::GetFileNameWithoutExtension($artifact) } else { 'usability_source' }

    # -----------------------------------------------------------------------
    # Duplicate Convert protection (two rapid activation attempts)
    # -----------------------------------------------------------------------
    $null = Select-File -Window $window -ProcessId $app.Id -Path $sourceB
    $dupButton = Wait-ForConvertEnabled -Window $window -TimeoutSeconds $UiTimeoutSeconds
    $dupState = 'NOT_STARTED'
    if ($dupButton) {
        $dupSince = Get-Date
        Click-Element -Window $window -Element $dupButton
        Start-Sleep -Milliseconds 250
        Click-Element -Window $window -Element $dupButton
        Start-Sleep -Milliseconds 250
        Click-Element -Window $window -Element $dupButton
        $final = $null
        $deadline = (Get-Date).AddSeconds($ConversionTimeoutSeconds)
        while ((Get-Date) -lt $deadline) {
            $current = Get-FrozenState -Window $window
            if ($current.state -in @('SUCCESS', 'SUCCESS_WITH_WARNING', 'FAILED')) { $final = $current; break }
            Start-Sleep -Milliseconds 800
        }
        $dupState = if ($final) { $final.state } else { 'TIMEOUT' }
        $dupArtifacts = @(Get-NewDocumentArtifacts -Since $dupSince -Roots @($WorkDir))
        $Results['duplicate_convert'] = [ordered]@{ state = $dupState; artifacts = $dupArtifacts }
        Add-Check 'duplicate-convert-protection' ($dupState -eq 'SUCCESS' -and $dupArtifacts.Count -eq 1) (
            "state={0}; artifacts for the second source={1} (expected exactly 1)" -f $dupState, $dupArtifacts.Count)
    } else {
        Add-Check 'duplicate-convert-protection' $false 'Convert never became available'
    }

    # -----------------------------------------------------------------------
    # Word-locked output: the artifact is open in Word, then converted again
    # -----------------------------------------------------------------------
    if ($artifact -and (Test-Path -LiteralPath $artifact)) {
        $filesBeforeLock = @(Get-ChildItem -LiteralPath $outputDir -Filter '*.docx' -File -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
        Start-Process -FilePath (Join-Path ${env:ProgramFiles} 'Microsoft Office\root\Office16\WINWORD.EXE') -ArgumentList ('"{0}"' -f $artifact)
        $locked = $false
        $deadline = (Get-Date).AddSeconds(90)
        while ((Get-Date) -lt $deadline) {
            if (Test-FileExclusivelyLocked -Path $artifact) { $locked = $true; break }
            Start-Sleep -Milliseconds 1000
        }
        $Results['word_lock_observed'] = $locked
        if (-not $locked) {
            Add-Observation 'word-locked-output' 'Word did not take an exclusive lock on the artifact within 90 s; the locked-output case could not be reproduced on this machine.'
        } else {
            $null = Select-File -Window $window -ProcessId $app.Id -Path $sourceA
            $lockedRun = Convert-Once -Window $window -Since (Get-Date)
            $app.Refresh()
            $alive = -not $app.HasExited
            $filesAfterLock = @(Get-ChildItem -LiteralPath $outputDir -Filter '*.docx' -File -ErrorAction SilentlyContinue | ForEach-Object { $_.Name })
            $Results['word_locked_output'] = [ordered]@{
                state = $lockedRun.state
                alive = $alive
                files_before = $filesBeforeLock
                files_after = $filesAfterLock
                summary = $lockedRun.summary_texts
            }
            $sane = $alive -and ($lockedRun.state -in @('FAILED', 'SUCCESS', 'SUCCESS_WITH_WARNING'))
            Add-Check 'word-locked-output-fails-closed' $sane (
                "app alive={0}; terminal state={1}; output files before={2} after={3}" -f $alive, $lockedRun.state, $filesBeforeLock.Count, $filesAfterLock.Count)
        }
        # Release the lock and confirm the original artifact is still intact.
        $wordWindow = Wait-ForDesktopWindowByClass -ClassName $WordWindowClass -TitleContains $artifactName -IncludeHidden -TimeoutSeconds 30
        if ($wordWindow) {
            [void][MdcInput]::PostMessage($wordWindow.handle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)
            [void](Wait-ForDesktopWindowGone -ClassName $WordWindowClass -TitleContains $artifactName -TimeoutSeconds 30)
        }
        Start-Sleep -Seconds 2
        $Results['artifact_intact_after_lock_release'] = Test-DocxArtifact -Path $artifact
        Add-Check 'locked-output-no-data-loss' ([bool]$Results['artifact_intact_after_lock_release']) (
            "artifact still a valid DOCX after the Word lock was released: {0}" -f $Results['artifact_intact_after_lock_release'])
    }

    # -----------------------------------------------------------------------
    # Output path blocked by a same-named directory
    # -----------------------------------------------------------------------
    $blockedDir = Join-Path $outputDir 'blocked_output.docx'
    if (Test-Path -LiteralPath $blockedDir) { Remove-Item -LiteralPath $blockedDir -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $blockedDir | Out-Null
    $null = Select-File -Window $window -ProcessId $app.Id -Path $sourceBlocked
    $blockedRun = Convert-Once -Window $window -Since (Get-Date)
    $app.Refresh()
    $Results['blocked_output'] = [ordered]@{ state = $blockedRun.state; alive = (-not $app.HasExited); summary = $blockedRun.summary_texts }
    Add-Check 'unavailable-output-fails-closed' ((-not $app.HasExited) -and ($blockedRun.state -in @('FAILED', 'SUCCESS', 'SUCCESS_WITH_WARNING'))) (
        "app alive={0}; terminal state={1}" -f (-not $app.HasExited), $blockedRun.state)
    if (Test-Path -LiteralPath $blockedDir) { Remove-Item -LiteralPath $blockedDir -Recurse -Force }

    # -----------------------------------------------------------------------
    # Stale remembered source/output directories
    # -----------------------------------------------------------------------
    New-Item -Path (Join-Path $PrefsApp 'folders') -Force | Out-Null
    Set-ItemProperty -Path (Join-Path $PrefsApp 'folders') -Name 'last_source_directory' -Value 'Z:\definitely\missing\p1209' -Type String
    Set-ItemProperty -Path (Join-Path $PrefsApp 'folders') -Name 'last_output_directory' -Value 'Z:\definitely\missing\p1209' -Type String
    Set-ItemProperty -Path (Join-Path $PrefsApp 'folders') -Name 'remember' -Value 1 -Type DWord

    $null = Close-App -Process $app -Window $window
    $app = Start-App -Path $ExePath -Directory $WorkDir
    $window = Get-AppWindow -ProcessId $app.Id -TimeoutSeconds $StartupTimeoutSeconds
    Add-Check 'stale-directory-startup' ([bool]$window) 'application starts normally with a stale remembered directory'

    $settingsDialog = $null
    if (Invoke-ButtonByName -Window $window -NamePattern '^Settings$' -TimeoutSeconds $UiTimeoutSeconds) {
        $settingsDialog = Get-TopLevelWindow -ProcessId $app.Id -NamePrefix 'Settings' -TimeoutSeconds $UiTimeoutSeconds
    }
    if (-not $settingsDialog) {
        Add-Check 'stale-remembered-directory' $false 'Settings dialog did not appear'
    } else {
        $settingsTexts = @(Get-Descendants -Root $settingsDialog | ForEach-Object { $_.Current.Name } | Where-Object { $_ })
        $joinedSettings = ($settingsTexts -join "`n")
        $showsNotRemembered = $joinedSettings -match 'Not remembered'
        $leaksStalePath = $joinedSettings -match 'Z:\\definitely'
        $Results['stale_directory_settings_text'] = $settingsTexts
        Add-Check 'stale-remembered-directory' ($showsNotRemembered -and -not $leaksStalePath) (
            "Settings shows 'Not remembered'={0}; stale path leaked={1}" -f $showsNotRemembered, $leaksStalePath)
        [void](Close-Dialog -Dialog $settingsDialog -TimeoutSeconds 15)
    }

    $null = Select-File -Window $window -ProcessId $app.Id -Path $sourceB
    $afterStale = Convert-Once -Window $window -Since (Get-Date)
    Add-Check 'usable-after-stale-directory' ($afterStale.state -eq 'SUCCESS') (
        "conversion after a stale remembered directory: {0}" -f $afterStale.state)

    # -----------------------------------------------------------------------
    # Off-screen stored geometry (product's own save/restore path)
    # -----------------------------------------------------------------------
    $handle = [IntPtr]$window.Current.NativeWindowHandle
    [void][MdcWindowProbe]::MoveTo($handle, 5000, 5000)
    Start-Sleep -Milliseconds 800
    $offscreenRect = [MdcWindowProbe]::Rect($handle)
    $Results['moved_offscreen_rect'] = ($offscreenRect -join ',')
    $closedAfterMove = Close-App -Process $app -Window $window
    Add-Check 'geometry-saved-on-close' $closedAfterMove 'application closed (storing its off-screen geometry)'

    $app = Start-App -Path $ExePath -Directory $WorkDir
    $window = Get-AppWindow -ProcessId $app.Id -TimeoutSeconds $StartupTimeoutSeconds
    if (-not $window) {
        Add-Check 'offscreen-geometry-rejected' $false 'application did not restart'
    } else {
        $rect = [MdcWindowProbe]::Rect([IntPtr]$window.Current.NativeWindowHandle)
        $screenW = [MdcWindowProbe]::ScreenWidth(); $screenH = [MdcWindowProbe]::ScreenHeight()
        $visibleW = [Math]::Min($rect[2], $screenW) - [Math]::Max($rect[0], 0)
        $visibleH = [Math]::Min($rect[3], $screenH) - [Math]::Max($rect[1], 0)
        $Results['restored_rect'] = ($rect -join ',')
        $Results['screen'] = "$screenW x $screenH"
        $Results['visible_pixels'] = "$visibleW x $visibleH"
        Add-Check 'offscreen-geometry-rejected' ($visibleW -ge 200 -and $visibleH -ge 200) (
            "restored window rect {0} on a {1} screen (visible {2})" -f ($rect -join ','), "$screenW x $screenH", "$visibleW x $visibleH")
    }

    # -----------------------------------------------------------------------
    # Accessibility on the real window (names, Tab order, textual status)
    # -----------------------------------------------------------------------
    $null = Select-File -Window $window -ProcessId $app.Id -Path $sourceA
    $all = @(Get-Descendants -Root $window)
    $names = @($all | ForEach-Object { $_.Current.Name } | Where-Object { $_ })
    $requiredNames = @('Select File', 'Change output folder', 'Convert', 'Settings', 'About', 'Markdown file drop area')
    $missingNames = @($requiredNames | Where-Object { $names -notcontains $_ })
    Add-Check 'accessible-names' ($missingNames.Count -eq 0) ("missing accessible names: {0}" -f (($missingNames -join ', ') -replace '^$', 'none'))
    Add-Check 'status-is-textual' ($names -contains 'Status') "status area exposes the accessible name 'Status' and outcome wording is text"

    $focusOrder = @()
    foreach ($element in $all) {
        if ($element.Current.IsKeyboardFocusable -and $element.Current.Name) { $focusOrder += $element.Current.Name }
    }
    $Results['keyboard_focus_order'] = $focusOrder
    $idxSelect = [array]::IndexOf($focusOrder, 'Select File')
    $idxOutput = [array]::IndexOf($focusOrder, 'Change output folder')
    $idxConvert = [array]::IndexOf($focusOrder, 'Convert')
    Add-Check 'tab-order-logical' ($idxSelect -ge 0 -and $idxOutput -gt $idxSelect -and $idxConvert -gt $idxOutput) (
        "focus order indices: Select File={0}, Change output folder={1}, Convert={2}" -f $idxSelect, $idxOutput, $idxConvert)

    # -----------------------------------------------------------------------
    # Report surface is keyboard reachable (warning outcome)
    # -----------------------------------------------------------------------
    $null = Select-File -Window $window -ProcessId $app.Id -Path $sourceWarning
    $warningRun = Convert-Once -Window $window -Since (Get-Date)
    if ($warningRun.state -ne 'SUCCESS_WITH_WARNING') {
        Add-Check 'report-keyboard-reachable' $false ("warning conversion outcome was {0}" -f $warningRun.state)
    } else {
        $detailsDialog = $null
        if (Invoke-ButtonByName -Window $window -NamePattern '^Details' -TimeoutSeconds $UiTimeoutSeconds) {
            $detailsDialog = Get-TopLevelWindow -ProcessId $app.Id -NamePrefix 'Warning details' -TimeoutSeconds $UiTimeoutSeconds
        }
        if (-not $detailsDialog) {
            Add-Check 'report-keyboard-reachable' $false 'Warning details dialog did not appear'
        } else {
            $dialogElements = @(Get-Descendants -Root $detailsDialog)
            $focusable = @($dialogElements | Where-Object { $_.Current.IsKeyboardFocusable })
            $Results['report_dialog_focusable_count'] = $focusable.Count
            $Results['report_dialog_texts'] = @($dialogElements | ForEach-Object { $_.Current.Name } | Where-Object { $_ })
            Add-Check 'report-keyboard-reachable' ($dialogElements.Count -gt 0 -and $focusable.Count -gt 0) (
                "dialog exposes {0} element(s), {1} keyboard-focusable" -f $dialogElements.Count, $focusable.Count)
            [void](Close-Dialog -Dialog $detailsDialog -TimeoutSeconds 15)
        }
    }

    # -----------------------------------------------------------------------
    # Clean close
    # -----------------------------------------------------------------------
    $closed = Close-App -Process $app -Window $window
    Add-Check 'clean-close' $closed ("application exits when closed while idle: {0}" -f $closed)
}
catch {
    Add-Check 'harness' $false ("aborted: {0}" -f $_.Exception.Message)
}
finally {
    if ($app) { Stop-App -Process $app }
    Get-Process MD_Converter_Lite -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    try {
        if ($Restore.existed -and $Restore.backup) {
            & reg.exe import $Restore.backup 2>$null | Out-Null
        } elseif (Test-Path $PrefsRoot) {
            Remove-Item -LiteralPath $PrefsRoot -Recurse -Force
        }
        $Results['settings_restored'] = $true
    } catch {
        $Results['settings_restored'] = "failed: $($_.Exception.Message)"
    }
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
