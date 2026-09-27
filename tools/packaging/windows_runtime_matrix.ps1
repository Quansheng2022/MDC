#requires -Version 5.1
<#
.SYNOPSIS
    Packaged Windows runtime verification matrix for MD Converter (P12-08).

.DESCRIPTION
    Drives the *installed* (or packaged) MD Converter GUI through the runtime
    behaviours that source-tree tests cannot prove, using the shared automation
    primitives in ``gui_automation.ps1``:

        A. startup, worker-active close protection, clean close
        C. settings persistence across a restart
        D/E. Open Document (Microsoft Word actually opens the file), Open Folder
        F. missing artifact fails closed (no fallback, no Word, no conversion)
        G. path robustness (spaces + non-ASCII path, installed app, foreign CWD)
        H. high-DPI smoke

    The script only performs real user actions against the packaged product and
    verifies the results; it changes no product behaviour and never edits the
    generated document.

.EXAMPLE
    powershell -File tools/packaging/windows_runtime_matrix.ps1 `
        -ExePath "$env:LOCALAPPDATA\Programs\MD_Converter\MD_Converter.exe" `
        -WorkDir "$env:TEMP\mdc_runtime" -EvidencePath "$env:TEMP\mdc_runtime.json"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ExePath,
    [string]$WorkDir,
    [string]$EvidencePath,
    [int]$StartupTimeoutSeconds = 60,
    [int]$UiTimeoutSeconds = 30,
    [int]$ConversionTimeoutSeconds = 900,
    [switch]$KeepOpen
)

. "$PSScriptRoot\gui_automation.ps1"

$MainWindowTitle = 'MD Converter'
$PrefsKey = 'HKCU:\Software\MD Converter'
$PrefsFoldersKey = "$PrefsKey\MD Converter\folders"
$WordWindowClass = 'OpusApp'
$ExplorerWindowClass = 'CabinetWClass'

$Results = [ordered]@{}
$Failures = New-Object System.Collections.ArrayList
$RestoreState = [ordered]@{ key_existed = $false; backup = $null }

function Write-Step {
    param([string]$Message)
    Write-Host ("[runtime] {0}" -f $Message)
}

function Add-Check {
    param([string]$Name, [bool]$Passed, $Detail)
    $Results[$Name] = [ordered]@{ passed = $Passed; detail = "$Detail" }
    if (-not $Passed) { [void]$Failures.Add($Name) }
    Write-Step ("{0} {1} :: {2}" -f ($(if ($Passed) { 'PASS' } else { 'FAIL' })), $Name, $Detail)
}

function Start-App {
    param([string]$Path, [string]$Directory)
    return Start-Process -FilePath $Path -WorkingDirectory $Directory -PassThru
}

function Stop-App {
    param($Process)
    try {
        $Process.Refresh()
        if (-not $Process.HasExited) { $Process.Kill() }
    } catch { }
}

function Get-AppWindow {
    param([int]$ProcessId, [int]$TimeoutSeconds = 60)
    return Get-TopLevelWindow -ProcessId $ProcessId -Name $MainWindowTitle -TimeoutSeconds $TimeoutSeconds
}

function Wait-ForNewWindowContaining {
    param(
        [string]$ClassName,
        [string[]]$ExcludeHandles,
        [string]$TitleContains,
        [int]$TimeoutSeconds = 60
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        foreach ($item in Get-DesktopWindowsByClass -ClassName $ClassName) {
            if ($ExcludeHandles -contains $item.handle) { continue }
            if ($TitleContains -and $item.title -notlike "*$TitleContains*") { continue }
            return $item
        }
        Start-Sleep -Milliseconds 500
    }
    return $null
}

function Get-SettingsDialog {
    param([int]$ProcessId, [int]$TimeoutSeconds = 30)
    return Get-TopLevelWindow -ProcessId $ProcessId -NamePrefix 'Settings' -TimeoutSeconds $TimeoutSeconds
}

function Open-SettingsDialog {
    param([System.Windows.Automation.AutomationElement]$Window, [int]$ProcessId)
    if (-not (Invoke-ButtonByName -Window $Window -NamePattern '^Settings$' -TimeoutSeconds $UiTimeoutSeconds)) {
        throw 'Settings button not available'
    }
    return Get-SettingsDialog -ProcessId $ProcessId -TimeoutSeconds $UiTimeoutSeconds
}

function Get-RememberCheckbox {
    param([System.Windows.Automation.AutomationElement]$Dialog)
    return Find-Element -Root $Dialog -NamePattern 'Remember the last folders I used' -TimeoutSeconds $UiTimeoutSeconds
}

function Get-ToggleState {
    param([System.Windows.Automation.AutomationElement]$Element)
    $pattern = $Element.GetCurrentPattern($Global:TogglePattern::Pattern)
    return $pattern.Current.ToggleState.ToString()
}

function Get-PreferenceValue {
    param([Parameter(Mandatory = $true)][string]$Name)
    $value = (Get-ItemProperty -Path $PrefsFoldersKey -Name $Name -ErrorAction SilentlyContinue).$Name
    return $value
}

# ---------------------------------------------------------------------------
# Preparation
# ---------------------------------------------------------------------------

$ExePath = (Resolve-Path -LiteralPath $ExePath).Path
if (-not $WorkDir) {
    $WorkDir = Join-Path $env:TEMP ("mdc_runtime_" + (Get-Date -Format 'yyyyMMdd_HHmmss'))
}
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null

# Non-ASCII + spaces path for the path-robustness check.
$RunToken = Get-Date -Format 'HHmmss'
$NonAsciiDir = Join-Path $WorkDir "MDC smoke ü 测试 $RunToken"
New-Item -ItemType Directory -Force -Path $NonAsciiDir | Out-Null
$DocumentTitle = "Runtime Matrix $RunToken"
$NonAsciiInput = Join-Path $NonAsciiDir "runtime smoke ü $RunToken.md"
@"
---
title: $DocumentTitle
date: 2026-09-27
---

# Runtime Matrix

Packaged runtime verification for **P12-08**.

- path robustness
- output actions
"@ | Set-Content -LiteralPath $NonAsciiInput -Encoding UTF8

# Snapshot the product's own settings key so verification leaves no trace.
if (Test-Path $PrefsKey) {
    $RestoreState.key_existed = $true
    $RestoreState.backup = Join-Path $WorkDir 'prefs_backup.reg'
    & reg.exe export "HKCU\Software\MD Converter" $RestoreState.backup /y | Out-Null
}

$Results['executable'] = $ExePath
$Results['work_dir'] = $WorkDir
$Results['non_ascii_dir'] = $NonAsciiDir
$Results['python_io_encoding_env'] = "$env:PYTHONIOENCODING"
$Results['started_at'] = (Get-Date).ToString('o')

$app = $null
$window = $null
$artifact = $null

try {
    # -----------------------------------------------------------------------
    # A + G. Startup, path robustness and a real conversion through the GUI
    # -----------------------------------------------------------------------
    $app = Start-App -Path $ExePath -Directory $WorkDir
    $window = Get-AppWindow -ProcessId $app.Id -TimeoutSeconds $StartupTimeoutSeconds
    Add-Check 'startup' ([bool]$window) ("main window visible (pid {0})" -f $app.Id)
    if (-not $window) { throw 'the packaged GUI did not start' }

    $windowRect = $window.Current.BoundingRectangle
    $Results['main_window_rect'] = "$([int]$windowRect.X),$([int]$windowRect.Y) $([int]$windowRect.Width)x$([int]$windowRect.Height)"

    # H. High-DPI smoke: every interactive control must be inside the window.
    $outside = New-Object System.Collections.ArrayList
    foreach ($element in Get-Descendants -Root $window) {
        if ($element.Current.ControlType -ne $Global:ControlType::Button) { continue }
        if (-not $element.Current.Name) { continue }
        $rect = $element.Current.BoundingRectangle
        if ($rect.Width -le 0 -or $rect.Height -le 0) { continue }
        $inside = ($rect.X -ge $windowRect.X -and $rect.Y -ge $windowRect.Y -and
                   ($rect.X + $rect.Width) -le ($windowRect.X + $windowRect.Width) -and
                   ($rect.Y + $rect.Height) -le ($windowRect.Y + $windowRect.Height))
        if (-not $inside) { [void]$outside.Add($element.Current.Name) }
    }
    Add-Check 'high-dpi-controls-in-bounds' ($outside.Count -eq 0) (
        "window $($Results['main_window_rect']); clipped controls: {0}" -f (($outside -join ', ') -replace '^$', 'none'))

    $conversion = Convert-MarkdownThroughGui -Window $window -ProcessId $app.Id `
        -InputMarkdown $NonAsciiInput -TimeoutSeconds $ConversionTimeoutSeconds
    $Results['conversion'] = $conversion
    Add-Check 'conversion-non-ascii-path' ($conversion.outcome.outcome -eq 'SUCCESS') (
        "outcome={0} after {1}s for a spaces+non-ASCII input path" -f $conversion.outcome.outcome, $conversion.outcome.seconds)

    $artifacts = @(Get-NewDocumentArtifacts -Since ([datetime]$Results['started_at']) -Roots @($NonAsciiDir, $WorkDir))
    $Results['artifacts'] = $artifacts
    Add-Check 'artifact-created' ($artifacts.Count -gt 0) ("{0} DOCX artifact(s)" -f $artifacts.Count)
    if ($artifacts.Count -gt 0) { $artifact = $artifacts[0] }

    $rememberedSource = Get-PreferenceValue -Name 'last_source_directory'
    $Results['pref_last_source_directory'] = $rememberedSource
    Add-Check 'preference-written-on-conversion' ($rememberedSource -like "*$RunToken*") (
        "product preference store remembered this run's source folder: {0}" -f $rememberedSource)

    # -----------------------------------------------------------------------
    # D. Open Document - Microsoft Word must actually open the artifact
    # -----------------------------------------------------------------------
    $artifactLeaf = if ($artifact) { [System.IO.Path]::GetFileNameWithoutExtension($artifact) } else { '' }
    $artifactExistedBefore = ($artifact -and (Test-Path -LiteralPath $artifact))
    $opened = Invoke-ButtonByName -Window $window -NamePattern '^Open Document$' -TimeoutSeconds $UiTimeoutSeconds
    $wordDocument = $null
    if ($opened -and $artifactLeaf) {
        # Microsoft Word loads the document in its own document window, which is
        # hidden while another Word document stays the active window - so hidden
        # OpusApp windows are matched as well.
        $wordDocument = Wait-ForDesktopWindowByClass -ClassName $WordWindowClass `
            -TitleContains $artifactLeaf -IncludeHidden -TimeoutSeconds 120
    }
    $lockedWhileWordHasIt = ($artifact -and (Test-FileExclusivelyLocked -Path $artifact))
    $artifactExistsAfter = ($artifact -and (Test-Path -LiteralPath $artifact))
    $Results['word_document_window'] = if ($wordDocument) { $wordDocument.title } else { $null }
    Add-Check 'open-document-word-opens' ([bool]$wordDocument) (
        "artifact existed before={0}; Word document window: {1}" -f $artifactExistedBefore,
        $(if ($wordDocument) { "'" + $wordDocument.title + "'" } else { 'none' }))
    Add-Check 'open-document-word-reads-file' ([bool]$lockedWhileWordHasIt) (
        "document held open by Word while displayed (exclusive lock observed): {0}" -f $lockedWhileWordHasIt)
    Add-Check 'artifact-persists-after-open' ($artifactExistedBefore -and $artifactExistsAfter) (
        "artifact present before and after opening")
    if ($wordDocument) {
        [void][MdcInput]::PostMessage($wordDocument.handle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)
        [void](Wait-ForDesktopWindowGone -ClassName $WordWindowClass -TitleContains $artifactLeaf -TimeoutSeconds 30)
    }
    $lockReleased = -not (Test-FileExclusivelyLocked -Path $artifact)
    Add-Check 'word-document-closed-lock-released' ([bool]$lockReleased) (
        "closing the Word document window released the file lock: {0}" -f $lockReleased)

    # -----------------------------------------------------------------------
    # E. Open Folder - the containing folder must actually open
    # -----------------------------------------------------------------------
    $explorerBefore = @(Get-DesktopWindowsByClass -ClassName $ExplorerWindowClass | ForEach-Object { $_.handle })
    $folderName = if ($artifact) { Split-Path -Leaf (Split-Path -Parent $artifact) } else { '' }
    $folderOpened = Invoke-ButtonByName -Window $window -NamePattern '^Open Folder$' -TimeoutSeconds $UiTimeoutSeconds
    $explorerWindow = $null
    if ($folderOpened) {
        $explorerWindow = Wait-ForNewWindowContaining -ClassName $ExplorerWindowClass `
            -ExcludeHandles $explorerBefore -TitleContains $folderName -TimeoutSeconds 60
    }
    $Results['explorer_window_title'] = if ($explorerWindow) { $explorerWindow.title } else { $null }
    Add-Check 'open-folder' ([bool]$explorerWindow) (
        "expected folder '{0}'; new Explorer window: {1}" -f $folderName,
        $(if ($explorerWindow) { "'" + $explorerWindow.title + "'" } else { 'none' }))
    if ($explorerWindow) {
        [void][MdcInput]::PostMessage($explorerWindow.handle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)
        Start-Sleep -Seconds 1
    }

    # -----------------------------------------------------------------------
    # F. Missing artifact must fail closed
    # -----------------------------------------------------------------------
    if ($artifact -and (Test-Path -LiteralPath $artifact)) {
        Remove-Item -LiteralPath $artifact -Force
    }
    $missingClicked = Invoke-ButtonByName -Window $window -NamePattern '^Open Document$' -TimeoutSeconds $UiTimeoutSeconds
    $notice = $null
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline -and -not $notice) {
        # Qt appends " - MD Converter" to the message-box title as well.
        $notice = Get-TopLevelWindow -ProcessId $app.Id -NamePrefix 'File not available' -TimeoutSeconds 2
    }
    $wordAfterMissing = Wait-ForDesktopWindowByClass -ClassName $WordWindowClass `
        -TitleContains $artifactLeaf -IncludeHidden -TimeoutSeconds 8
    Start-Sleep -Seconds 8
    $app.Refresh()
    $artifactRecreated = Test-Path -LiteralPath $artifact
    $Results['missing_artifact_dialog'] = if ($notice) { $notice.Current.Name } else { $null }
    Add-Check 'missing-artifact-fails-closed' (($null -ne $notice) -and (-not $wordAfterMissing) -and (-not $artifactRecreated) -and (-not $app.HasExited)) (
        "notice={0}; new Word window={1}; artifact recreated={2}; app alive={3}" -f
        $(if ($notice) { 'shown' } else { 'missing' }), $wordAfterMissing, $artifactRecreated, (-not $app.HasExited))
    if ($notice) { [void](Close-Dialog -Dialog $notice -TimeoutSeconds 10) }

    # -----------------------------------------------------------------------
    # C. Settings persistence across a restart
    # -----------------------------------------------------------------------
    $settingsDialog = Open-SettingsDialog -Window $window -ProcessId $app.Id
    $originalToggle = $null
    if ($settingsDialog) {
        $checkbox = Get-RememberCheckbox -Dialog $settingsDialog
        if ($checkbox) {
            $originalToggle = Get-ToggleState -Element $checkbox
            $Results['settings_toggle_before'] = $originalToggle
            if ($originalToggle -ne 'On') { Click-Element -Window $settingsDialog -Element $checkbox }
            Start-Sleep -Milliseconds 400
            $newToggle = Get-ToggleState -Element (Get-RememberCheckbox -Dialog $settingsDialog)
            $Results['settings_toggle_set'] = $newToggle
            [void](Invoke-ButtonByName -Window $settingsDialog -NamePattern '^Save$' -TimeoutSeconds $UiTimeoutSeconds)
            Start-Sleep -Milliseconds 800
            $Results['pref_remember_after_save'] = Get-PreferenceValue -Name 'remember'
        }
    }
    Add-Check 'settings-saved' ($null -ne $originalToggle) (
        "remember-folders checkbox: before={0}, set to On and saved" -f $originalToggle)

    Close-WindowElement -Element $window
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline) {
        $app.Refresh(); if ($app.HasExited) { break }; Start-Sleep -Milliseconds 400
    }
    $app.Refresh()
    Add-Check 'clean-close-and-restart-step' ([bool]$app.HasExited) 'application closed cleanly before restart'

    $app = Start-App -Path $ExePath -Directory $WorkDir
    $window = Get-AppWindow -ProcessId $app.Id -TimeoutSeconds $StartupTimeoutSeconds
    Add-Check 'restart' ([bool]$window) ("restarted application window visible (pid {0})" -f $app.Id)

    $settingsDialog = Open-SettingsDialog -Window $window -ProcessId $app.Id
    $restoredToggle = $null
    $rememberedSources = @()
    if ($settingsDialog) {
        $checkbox = Get-RememberCheckbox -Dialog $settingsDialog
        if ($checkbox) { $restoredToggle = Get-ToggleState -Element $checkbox }
        # Match on the per-run token: the product stores the long path form while
        # the shell may hand out the 8.3 short form for the temp directory.
        $rememberedSources = @(Get-TextNames -Root $settingsDialog | Where-Object { $_ -like "*$RunToken*" })
        [void](Close-Dialog -Dialog $settingsDialog -TimeoutSeconds 15)
    }
    $Results['settings_toggle_after_restart'] = $restoredToggle
    $Results['remembered_folder_texts'] = $rememberedSources
    Add-Check 'settings-persist-across-restart' ($restoredToggle -eq 'On') (
        "remember-folders after restart = {0}" -f $restoredToggle)
    Add-Check 'remembered-folders-restored' ($rememberedSources.Count -gt 0) (
        "{0} remembered-folder value(s) shown by the restarted app" -f $rememberedSources.Count)

    # -----------------------------------------------------------------------
    # A. Worker-active close protection
    # -----------------------------------------------------------------------
    $closeProtectedInput = Join-Path $NonAsciiDir 'close protection ü.md'
    "# Close protection`n`nSecond real conversion for the close-protection check.`n" |
        Set-Content -LiteralPath $closeProtectedInput -Encoding UTF8
    $selection = Select-SourceFile -Window $window -ProcessId $app.Id -FilePath $closeProtectedInput
    $convertButton = Wait-ForConvertEnabled -Window $window
    $protected = $false
    $outcome = $null
    if ($convertButton) {
        Click-Element -Window $window -Element $convertButton
        Start-Sleep -Milliseconds 700
        Close-WindowElement -Element $window
        Start-Sleep -Seconds 3
        $app.Refresh()
        $protected = -not $app.HasExited
        $outcome = Wait-ForConversionOutcome -Window $window -TimeoutSeconds $ConversionTimeoutSeconds
    }
    Add-Check 'worker-active-close-protection' $protected (
        "window close during an active conversion did not terminate the application (still running={0})" -f $protected)
    $Results['close_protection_outcome'] = $outcome
    Add-Check 'close-protection-conversion-completes' ($outcome -and $outcome.outcome -eq 'SUCCESS') (
        "conversion outcome after protected close: {0}" -f $(if ($outcome) { $outcome.outcome } else { 'n/a' }))

    Close-WindowElement -Element $window
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline) {
        $app.Refresh(); if ($app.HasExited) { break }; Start-Sleep -Milliseconds 400
    }
    $app.Refresh()
    Add-Check 'clean-close' ([bool]$app.HasExited) 'application exits when closed while idle'
}
catch {
    Add-Check 'runtime-matrix' $false ("aborted: {0}" -f $_.Exception.Message)
}
finally {
    if ($app) { Stop-App -Process $app }
    # Restore the product's own settings so verification leaves no trace.
    try {
        if ($RestoreState.key_existed -and $RestoreState.backup) {
            & reg.exe import $RestoreState.backup 2>$null | Out-Null
        } elseif (Test-Path $PrefsKey) {
            Remove-Item -LiteralPath $PrefsKey -Recurse -Force
        }
        $Results['settings_restored'] = $true
    } catch {
        $Results['settings_restored'] = "failed: $($_.Exception.Message)"
    }
    if (-not $KeepOpen) { Get-Process MD_Converter -ErrorAction SilentlyContinue | ForEach-Object { $_.Kill() } }
}

$Results['finished_at'] = (Get-Date).ToString('o')
$Results['failed_checks'] = @($Failures)
$Results['status'] = $(if ($Failures.Count -eq 0) { 'PASS' } else { 'FAIL' })

if ($EvidencePath) {
    $directory = Split-Path -Parent $EvidencePath
    if ($directory) { New-Item -ItemType Directory -Force -Path $directory | Out-Null }
    $Results | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $EvidencePath -Encoding UTF8
    Write-Step ("evidence written to {0}" -f $EvidencePath)
}

Write-Host ""
Write-Host ("RESULT: {0} ({1} failing check(s))" -f $Results['status'], $Failures.Count)
if ($Failures.Count -gt 0) { exit 1 }
exit 0
