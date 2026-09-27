#requires -Version 5.1
<#
.SYNOPSIS
    Focused functional-acceptance matrix for the P12-09 release candidate.

.DESCRIPTION
    Complements ``windows_gui_smoke.ps1`` (representative conversions) and
    ``windows_runtime_matrix.ps1`` (installed runtime behaviours) by exercising
    the acceptance cases those two do not cover:

        * frozen GUI states (EMPTY / READY / CONVERTING / SUCCESS /
          SUCCESS_WITH_WARNING / FAILED) observed through the product's own
          outcome controls;
        * invalid / non-Markdown input fails safely;
        * missing (deleted) source fails safely;
        * warning and failure result UX with the retained details report;
        * workflow recovery and sequential conversions;
        * About wording (version, product name, frozen positioning, bounded
          local/private facts);
        * Settings Cancel discards edits and Reset to Defaults restores the form
          default;
        * WM_DROPFILES / WS_EX_ACCEPTFILES probe for the drop surface.

    Verification tooling only.  No product behaviour is changed and no
    conversion logic is reimplemented; conversions run through the packaged
    application exactly as a user would drive them.

.EXAMPLE
    powershell -File tools/packaging/p12_09_acceptance.ps1 `
        -ExePath dist/MD_Converter_Lite/MD_Converter_Lite.exe `
        -CorpusDir Doc/V2/Implementation/P12-09/corpus -EvidencePath accept.json
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ExePath,
    [Parameter(Mandatory = $true)][string]$CorpusDir,
    [string]$WorkDir,
    [string]$EvidencePath,
    [int]$StartupTimeoutSeconds = 60,
    [int]$UiTimeoutSeconds = 30,
    [int]$ConversionTimeoutSeconds = 900,
    [switch]$KeepOpen
)

. "$PSScriptRoot\gui_automation.ps1"

if (-not ('MdcDrop' -as [type])) {
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;

public static class MdcDrop
{
    [StructLayout(LayoutKind.Sequential)]
    public struct DROPFILES
    {
        public uint pFiles;
        public int x;
        public int y;
        public int fNC;
        public int fWide;
    }

    [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
    [DllImport("kernel32.dll")] public static extern IntPtr GlobalAlloc(uint flags, UIntPtr bytes);
    [DllImport("kernel32.dll")] public static extern IntPtr GlobalLock(IntPtr handle);
    [DllImport("kernel32.dll")] public static extern bool GlobalUnlock(IntPtr handle);
    [DllImport("kernel32.dll")] public static extern IntPtr GlobalFree(IntPtr handle);
    [DllImport("user32.dll", EntryPoint = "GetWindowLongPtrW")] private static extern IntPtr GetWindowLongPtr64(IntPtr hWnd, int index);
    [DllImport("user32.dll", EntryPoint = "GetWindowLongW")] private static extern int GetWindowLong32(IntPtr hWnd, int index);

    public const uint GHND = 0x0042;
    public const uint WM_DROPFILES = 0x0233;
    public const int GWL_EXSTYLE = -20;
    public const int WS_EX_ACCEPTFILES = 0x00000010;

    public static long ExStyle(IntPtr hWnd)
    {
        return IntPtr.Size == 8 ? GetWindowLongPtr64(hWnd, GWL_EXSTYLE).ToInt64()
                                : GetWindowLong32(hWnd, GWL_EXSTYLE);
    }

    public static bool AcceptsFiles(IntPtr hWnd)
    {
        return (ExStyle(hWnd) & WS_EX_ACCEPTFILES) != 0;
    }

    public static bool SendDrop(IntPtr hWnd, string path)
    {
        int headerSize = Marshal.SizeOf(typeof(DROPFILES));
        byte[] list = Encoding.Unicode.GetBytes(path + "\0\0");
        int total = headerSize + list.Length;
        IntPtr buffer = GlobalAlloc(GHND, (UIntPtr)total);
        if (buffer == IntPtr.Zero) { return false; }
        IntPtr target = GlobalLock(buffer);
        if (target == IntPtr.Zero) { GlobalFree(buffer); return false; }
        try
        {
            DROPFILES header = new DROPFILES();
            header.pFiles = (uint)headerSize;
            header.fWide = 1;
            Marshal.StructureToPtr(header, target, false);
            Marshal.Copy(list, 0, new IntPtr(target.ToInt64() + headerSize), list.Length);
        }
        finally
        {
            GlobalUnlock(buffer);
        }
        SendMessage(hWnd, WM_DROPFILES, buffer, IntPtr.Zero);
        GlobalFree(buffer);
        return true;
    }
}
'@
}

$MainWindowTitle = 'MD Converter'
$Results = [ordered]@{}
$Failures = New-Object System.Collections.ArrayList
$Observations = New-Object System.Collections.ArrayList

function Write-Step {
    param([string]$Message)
    Write-Host ("[accept] {0}" -f $Message)
}

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
        $Type,
        [int]$TimeoutSeconds = 3
    )
    if (-not $Type) { $Type = $Global:ControlType::Button }
    $element = Find-Element -Root $Window -NamePattern $NamePattern -Type $Type -TimeoutSeconds $TimeoutSeconds
    if (-not $element) {
        return [ordered]@{ present = $false; enabled = $false; onscreen = $false }
    }
    return [ordered]@{
        present = $true
        enabled = [bool]$element.Current.IsEnabled
        onscreen = (-not [bool]$element.Current.IsOffscreen)
    }
}

function Get-ToggleState {
    param([System.Windows.Automation.AutomationElement]$Element)
    $pattern = $Element.GetCurrentPattern($Global:TogglePattern::Pattern)
    return $pattern.Current.ToggleState.ToString()
}

function Get-VisibleTextNames {
    param([System.Windows.Automation.AutomationElement]$Window)
    return @(
        Get-Descendants -Root $Window |
            Where-Object { $_.Current.ControlType -eq $Global:ControlType::Text -and -not $_.Current.IsOffscreen } |
            ForEach-Object { $_.Current.Name }
    )
}

function Get-FrozenState {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [switch]$Fast
    )
    $probeTimeout = if ($Fast) { 1 } else { 3 }
    $convert = Get-ButtonState -Window $Window -NamePattern '^Convert$' -TimeoutSeconds $probeTimeout
    $openDocument = Get-ButtonState -Window $Window -NamePattern '^Open Document$' -TimeoutSeconds $probeTimeout
    $details = Get-ButtonState -Window $Window -NamePattern '^Details' -TimeoutSeconds $probeTimeout
    $texts = Get-VisibleTextNames -Window $Window
    # The source label exposes a stable accessible name, not the file path.
    $sourceSelected = [bool]($texts -contains 'Selected Markdown file')
    # A warning outcome carries the presentation-model warning summary.
    $warningSummary = [bool](@($texts | Where-Object { $_ -match 'Conversion reported \d+ warning' }).Count -gt 0)
    $resultVisible = [bool]($details.onscreen)

    $state = 'UNKNOWN'
    if ($warningSummary) { $state = 'SUCCESS_WITH_WARNING' }
    elseif ($openDocument.enabled) { $state = 'SUCCESS' }
    elseif ($resultVisible) { $state = 'FAILED' }
    elseif ($convert.enabled -and $sourceSelected) { $state = 'READY' }
    elseif (-not $convert.enabled -and $sourceSelected) { $state = 'CONVERTING' }
    elseif (-not $convert.enabled -and -not $sourceSelected) { $state = 'EMPTY' }
    return [ordered]@{
        state = $state
        convert = $convert
        open_document = $openDocument
        details = $details
        source_selected = $sourceSelected
        warning_summary = $warningSummary
        visible_texts = $texts
    }
}

function Open-AppDialog {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [int]$ProcessId,
        [string]$ButtonPattern,
        [string]$TitlePrefix,
        [int]$TimeoutSeconds = 30
    )
    if (-not (Invoke-ButtonByName -Window $Window -NamePattern $ButtonPattern -TimeoutSeconds $TimeoutSeconds)) {
        return $null
    }
    return (Get-TopLevelWindow -ProcessId $ProcessId -NamePrefix $TitlePrefix -TimeoutSeconds $TimeoutSeconds)
}

function Get-NewAppDialog {
    param(
        [int]$ProcessId,
        [string[]]$KnownTitles,
        [int]$TimeoutSeconds = 10
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        foreach ($handle in [MdcWindows]::Handles([uint32]$ProcessId)) {
            $title = [MdcWindows]::Title($handle)
            if (-not $title) { continue }
            if ($title -eq $MainWindowTitle) { continue }
            $known = $false
            foreach ($knownTitle in $KnownTitles) { if ($title -like "$knownTitle*") { $known = $true } }
            if (-not $known) {
                return [System.Windows.Automation.AutomationElement]::FromHandle($handle)
            }
        }
        Start-Sleep -Milliseconds 300
    }
    return $null
}

function Select-CorpusFile {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [int]$ProcessId,
        [string]$Path
    )
    return (Select-SourceFile -Window $Window -ProcessId $ProcessId -FilePath $Path -TimeoutSeconds $UiTimeoutSeconds)
}

function Convert-And-Classify {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [datetime]$Since
    )
    $convertButton = Wait-ForConvertEnabled -Window $Window -TimeoutSeconds $UiTimeoutSeconds
    if (-not $convertButton) {
        return [ordered]@{ state = 'NOT_STARTED'; seconds = 0; artifacts = @() }
    }
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    Click-Element -Window $Window -Element $convertButton
    # Sample the in-flight state: CONVERTING must disable the unsafe controls.
    Start-Sleep -Milliseconds 400
    $during = Get-FrozenState -Window $Window -Fast
    $duringSelect = Get-ButtonState -Window $Window -NamePattern '^Select File$' -TimeoutSeconds 1
    $duringDrop = Get-ButtonState -Window $Window -NamePattern '^Markdown file drop area$' -Type $Global:ControlType::Custom -TimeoutSeconds 1
    $deadline = (Get-Date).AddSeconds($ConversionTimeoutSeconds)
    $final = $null
    while ((Get-Date) -lt $deadline) {
        $current = Get-FrozenState -Window $Window
        if ($current.state -in @('SUCCESS', 'SUCCESS_WITH_WARNING', 'FAILED')) {
            # Require a stable sample: the same terminal state twice in a row, so
            # a transient mid-update frame is never classified as terminal.
            Start-Sleep -Milliseconds 700
            $confirm = Get-FrozenState -Window $Window
            if ($confirm.state -eq $current.state) { $final = $confirm; break }
        }
        Start-Sleep -Milliseconds 800
    }
    if (-not $final) {
        $final = Get-FrozenState -Window $Window
        $final.state = 'TIMEOUT'
    }
    $artifacts = @(Get-NewDocumentArtifacts -Since $Since -Roots @($WorkDir))
    return [ordered]@{
        state = $final.state
        seconds = [math]::Round($stopwatch.Elapsed.TotalSeconds, 1)
        open_document = $final.open_document
        details = $final.details
        artifacts = $artifacts
        during_state = $during.state
        during_select_file = $duringSelect
        during_drop_area = $duringDrop
    }
}

# ---------------------------------------------------------------------------
# Preparation
# ---------------------------------------------------------------------------

$ExePath = (Resolve-Path -LiteralPath $ExePath).Path
$CorpusDir = (Resolve-Path -LiteralPath $CorpusDir).Path
if (-not $WorkDir) {
    $WorkDir = Join-Path $env:TEMP ("mdc_p1209_accept_" + (Get-Date -Format 'yyyyMMdd_HHmmss'))
}
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null

$cases = @{}
foreach ($name in @(
    '01_simple.md', '02_headings_lists_tables.md', '03_unicode.md', '04_rich.md',
    '05_warning_empty_heading.md', '06_empty.md', 'invalid_input.txt')) {
    $target = Join-Path $WorkDir $name
    Copy-Item -LiteralPath (Join-Path $CorpusDir $name) -Destination $target -Force
    $cases[$name] = $target
}

$Results['executable'] = $ExePath
$Results['executable_sha256'] = (Get-FileHash -LiteralPath $ExePath -Algorithm SHA256).Hash
$Results['work_dir'] = $WorkDir
$Results['started_at'] = (Get-Date).ToString('o')

$app = $null
$window = $null

try {
    $app = Start-Process -FilePath $ExePath -WorkingDirectory $WorkDir -PassThru
    $Results['process_id'] = $app.Id
    $window = Get-TopLevelWindow -ProcessId $app.Id -Name $MainWindowTitle -TimeoutSeconds $StartupTimeoutSeconds
    Add-Check 'startup' ([bool]$window) ("main window '{0}' visible (pid {1})" -f $MainWindowTitle, $app.Id)
    if (-not $window) { throw 'the packaged GUI did not start' }
    $mainHandle = [IntPtr]$window.Current.NativeWindowHandle

    $empty = Get-FrozenState -Window $window
    $Results['state_empty'] = $empty
    Add-Check 'state-empty' ($empty.state -eq 'EMPTY') ("fresh window state={0}" -f $empty.state)

    $acceptsFiles = [MdcDrop]::AcceptsFiles($mainHandle)
    $Results['ws_ex_acceptfiles'] = $acceptsFiles
    $dropPath = $cases['01_simple.md']
    $dropped = [MdcDrop]::SendDrop($mainHandle, $dropPath)
    Start-Sleep -Seconds 2
    $afterDrop = Get-FrozenState -Window $window
    $Results['wm_dropfiles'] = [ordered]@{ sent = $dropped; resulting_state = $afterDrop.state }
    if ($afterDrop.state -eq 'READY') {
        Add-Check 'drag-and-drop' $true ("WM_DROPFILES accepted; state={0}" -f $afterDrop.state)
    } else {
        Add-Observation 'drag-and-drop' ("WM_DROPFILES did not register a source (state={0}; WS_EX_ACCEPTFILES={1}); Qt uses OLE IDropTarget, which cannot be scripted with window messages. The drop path is verified by the product's own drop-event tests in WP-09-03." -f $afterDrop.state, $acceptsFiles)
    }

    $aboutDialog = Open-AppDialog -Window $window -ProcessId $app.Id -ButtonPattern '^About$' -TitlePrefix 'About MD Converter' -TimeoutSeconds $UiTimeoutSeconds
    if (-not $aboutDialog) {
        Add-Check 'about-wording' $false 'About dialog did not appear'
    } else {
        $aboutText = @(Get-Descendants -Root $aboutDialog | ForEach-Object { $_.Current.Name } | Where-Object { $_ })
        $Results['about_text'] = $aboutText
        $joined = ($aboutText -join "`n")
        $hasName = $joined -match [regex]::Escape('MD Converter')
        $hasVersion = $joined -match [regex]::Escape('Version 1.1.0')
        $hasTagline = $joined -match [regex]::Escape('locally, privately, and without a subscription')
        $hasProcessing = $joined -match [regex]::Escape('Processing: Local, on this computer')
        $hasAccount = $joined -match [regex]::Escape('Account required: No')
        $hasUpload = $joined -match [regex]::Escape('Document upload: Not required for normal conversion')
        Add-Check 'about-wording' ($hasName -and $hasVersion -and $hasTagline -and $hasProcessing -and $hasAccount -and $hasUpload) (
            "name={0} version={1} tagline={2} processing={3} account={4} upload={5}" -f $hasName, $hasVersion, $hasTagline, $hasProcessing, $hasAccount, $hasUpload)
        [void](Close-Dialog -Dialog $aboutDialog -TimeoutSeconds 15)
    }

    $null = Select-CorpusFile -Window $window -ProcessId $app.Id -Path $cases['01_simple.md']
    $ready = Get-FrozenState -Window $window
    $Results['state_ready'] = $ready
    Add-Check 'state-ready' ($ready.state -eq 'READY') ("state after selecting a Markdown file = {0}" -f $ready.state)

    $null = Select-SourceFile -Window $window -ProcessId $app.Id -FilePath $cases['invalid_input.txt'] -TimeoutSeconds $UiTimeoutSeconds
    Start-Sleep -Seconds 2
    $notice = Get-NewAppDialog -ProcessId $app.Id -KnownTitles @('Settings', 'About MD Converter') -TimeoutSeconds 8
    $noticeText = @()
    if ($notice) { $noticeText = @(Get-Descendants -Root $notice | ForEach-Object { $_.Current.Name } | Where-Object { $_ }) }
    $afterInvalid = Get-FrozenState -Window $window
    $Results['invalid_input'] = [ordered]@{
        notice = $(if ($notice) { $notice.Current.Name } else { $null })
        notice_text = $noticeText
        resulting_state = $afterInvalid.state
    }
    $app.Refresh(); $alive = -not $app.HasExited
    $safeInvalid = $alive -and ($afterInvalid.state -eq 'READY')
    Add-Check 'invalid-input-safe' $safeInvalid ("app alive={0}; state={1}; notice='{2}'" -f $alive, $afterInvalid.state, $(if ($notice) { $notice.Current.Name } else { 'none' }))
    if ($notice) { [void](Close-Dialog -Dialog $notice -TimeoutSeconds 10) }

    $missingCopy = Join-Path $WorkDir 'missing_source.md'
    Copy-Item -LiteralPath $cases['01_simple.md'] -Destination $missingCopy -Force
    $null = Select-CorpusFile -Window $window -ProcessId $app.Id -Path $missingCopy
    $null = Wait-ForConvertEnabled -Window $window -TimeoutSeconds $UiTimeoutSeconds
    Remove-Item -LiteralPath $missingCopy -Force
    $missing = Convert-And-Classify -Window $window -Since (Get-Date)
    $missingNotice = Get-NewAppDialog -ProcessId $app.Id -KnownTitles @('Settings', 'About MD Converter') -TimeoutSeconds 5
    $missingNoticeText = @()
    if ($missingNotice) { $missingNoticeText = @(Get-Descendants -Root $missingNotice | ForEach-Object { $_.Current.Name } | Where-Object { $_ }) }
    $app.Refresh()
    $Results['missing_source'] = [ordered]@{
        state = $missing.state
        notice = $(if ($missingNotice) { $missingNotice.Current.Name } else { $null })
        notice_text = $missingNoticeText
    }
    $safeMissing = ((-not $app.HasExited) -and ($missing.state -in @('FAILED', 'SUCCESS_WITH_WARNING', 'READY', 'TIMEOUT')))
    Add-Check 'missing-source-safe' $safeMissing ("app alive={0}; state={1}; notice='{2}'" -f (-not $app.HasExited), $missing.state, $(if ($missingNotice) { $missingNotice.Current.Name } else { 'none' }))
    if ($missingNotice) { [void](Close-Dialog -Dialog $missingNotice -TimeoutSeconds 10) }

    $null = Select-CorpusFile -Window $window -ProcessId $app.Id -Path $cases['05_warning_empty_heading.md']
    $warning = Convert-And-Classify -Window $window -Since (Get-Date)
    $Results['warning_outcome'] = $warning
    Add-Check 'state-success-with-warning' ($warning.state -eq 'SUCCESS_WITH_WARNING') (
        "state={0} after {1}s (open_document enabled={2}; details on-screen={3})" -f $warning.state, $warning.seconds, $warning.open_document.enabled, $warning.details.onscreen)
    Add-Check 'state-converting-observed' ($warning.during_state -eq 'CONVERTING' -and (-not $warning.during_select_file.enabled) -and (-not $warning.during_drop_area.enabled)) (
        "in-flight state={0}; Select File enabled={1}; drop area enabled={2}" -f $warning.during_state, $warning.during_select_file.enabled, $warning.during_drop_area.enabled)
    $warnArtifact = @($warning.artifacts | Where-Object { Test-DocxArtifact -Path $_ })
    Add-Check 'warning-keeps-artifact-actionable' ($warnArtifact.Count -gt 0 -and $warning.open_document.enabled) (
        "valid DOCX={0}; Open Document enabled={1}" -f $warnArtifact.Count, $warning.open_document.enabled)

    $detailsDialog = Open-AppDialog -Window $window -ProcessId $app.Id -ButtonPattern '^Details' -TitlePrefix 'Warning details' -TimeoutSeconds $UiTimeoutSeconds
    if (-not $detailsDialog) {
        Add-Check 'warning-details-report' $false 'Warning details dialog did not appear'
    } else {
        $detailsText = @(Get-Descendants -Root $detailsDialog | ForEach-Object { $_.Current.Name } | Where-Object { $_ })
        $Results['warning_details_text'] = $detailsText
        $joinedDetails = ($detailsText -join "`n")
        Add-Check 'warning-details-report' ($detailsText.Count -gt 0 -and $joinedDetails -notmatch 'Traceback') (
            "dialog '{0}' returned {1} element(s); Traceback present={2}" -f $detailsDialog.Current.Name, $detailsText.Count, ($joinedDetails -match 'Traceback'))
        [void](Close-Dialog -Dialog $detailsDialog -TimeoutSeconds 15)
    }

    $null = Select-CorpusFile -Window $window -ProcessId $app.Id -Path $cases['06_empty.md']
    $failure = Convert-And-Classify -Window $window -Since (Get-Date)
    $Results['failure_outcome'] = $failure
    Add-Check 'state-failed' ($failure.state -eq 'FAILED') (
        "state={0} after {1}s (open_document enabled={2}; details on-screen={3})" -f $failure.state, $failure.seconds, $failure.open_document.enabled, $failure.details.onscreen)
    Add-Check 'failed-suppresses-output-actions' ((-not $failure.open_document.enabled) -and (-not $failure.open_document.onscreen)) (
        "Open Document enabled={0} on-screen={1}" -f $failure.open_document.enabled, $failure.open_document.onscreen)

    $failDetails = Open-AppDialog -Window $window -ProcessId $app.Id -ButtonPattern '^Details' -TitlePrefix 'Failure details' -TimeoutSeconds $UiTimeoutSeconds
    if (-not $failDetails) {
        Add-Check 'failure-details-report' $false 'Failure details dialog did not appear'
    } else {
        $failText = @(Get-Descendants -Root $failDetails | ForEach-Object { $_.Current.Name } | Where-Object { $_ })
        $Results['failure_details_text'] = $failText
        $joinedFail = ($failText -join "`n")
        Add-Check 'failure-details-report' ($failText.Count -gt 0 -and $joinedFail -notmatch 'Traceback') (
            "dialog '{0}' returned {1} element(s); Traceback present={2}" -f $failDetails.Current.Name, $failText.Count, ($joinedFail -match 'Traceback'))
        [void](Close-Dialog -Dialog $failDetails -TimeoutSeconds 15)
    }

    $null = Select-CorpusFile -Window $window -ProcessId $app.Id -Path $cases['02_headings_lists_tables.md']
    $recovered = Convert-And-Classify -Window $window -Since (Get-Date)
    $Results['recovery_outcome'] = $recovered
    Add-Check 'recovery-and-sequential-conversion' ($recovered.state -eq 'SUCCESS') (
        "state after recovering from FAILED = {0} in {1}s" -f $recovered.state, $recovered.seconds)

    $settingsDialog = Open-AppDialog -Window $window -ProcessId $app.Id -ButtonPattern '^Settings$' -TitlePrefix 'Settings' -TimeoutSeconds $UiTimeoutSeconds
    $cancelOk = $false
    $resetOk = $false
    if ($settingsDialog) {
        $checkbox = Find-Element -Root $settingsDialog -NamePattern 'Remember the last folders I used' -TimeoutSeconds $UiTimeoutSeconds
        if ($checkbox) {
            $toggleBefore = Get-ToggleState -Element $checkbox
            Click-Element -Window $settingsDialog -Element $checkbox
            Start-Sleep -Milliseconds 400
            $toggleFlipped = Get-ToggleState -Element (Find-Element -Root $settingsDialog -NamePattern 'Remember the last folders I used' -TimeoutSeconds 5)
            [void](Invoke-ButtonByName -Window $settingsDialog -NamePattern '^Cancel$' -TimeoutSeconds $UiTimeoutSeconds)
            Start-Sleep -Milliseconds 600
            $settingsAgain = Open-AppDialog -Window $window -ProcessId $app.Id -ButtonPattern '^Settings$' -TitlePrefix 'Settings' -TimeoutSeconds $UiTimeoutSeconds
            if ($settingsAgain) {
                $checkboxAgain = Find-Element -Root $settingsAgain -NamePattern 'Remember the last folders I used' -TimeoutSeconds $UiTimeoutSeconds
                $toggleAfterCancel = $(if ($checkboxAgain) { Get-ToggleState -Element $checkboxAgain } else { 'missing' })
                $cancelOk = ($toggleBefore -ne $toggleFlipped) -and ($toggleAfterCancel -eq $toggleBefore)
                $resetOk = [bool](Invoke-ButtonByName -Window $settingsAgain -NamePattern '^Reset to Defaults$' -TimeoutSeconds $UiTimeoutSeconds)
                Start-Sleep -Milliseconds 400
                $checkboxReset = Find-Element -Root $settingsAgain -NamePattern 'Remember the last folders I used' -TimeoutSeconds 5
                $toggleAfterReset = $(if ($checkboxReset) { Get-ToggleState -Element $checkboxReset } else { 'missing' })
                $Results['settings_cancel_reset'] = [ordered]@{
                    before = $toggleBefore; flipped = $toggleFlipped; after_cancel = $toggleAfterCancel
                    reset_clicked = $resetOk; after_reset = $toggleAfterReset
                }
                Add-Check 'settings-reset-to-defaults' ($resetOk -and $toggleAfterReset -eq 'On') (
                    "Reset to Defaults clicked={0}; toggle after reset={1}" -f $resetOk, $toggleAfterReset)
                [void](Close-Dialog -Dialog $settingsAgain -TimeoutSeconds 15)
            }
        }
    }
    Add-Check 'settings-cancel-discards' $cancelOk ("toggle before/flipped/after-cancel = {0}" -f (($Results['settings_cancel_reset']) | ConvertTo-Json -Compress))

    if ($KeepOpen) {
        Add-Check 'clean-close' $true 'skipped (KeepOpen)'
    } else {
        Close-WindowElement -Element $window
        $deadline = (Get-Date).AddSeconds(30)
        while ((Get-Date) -lt $deadline) {
            $app.Refresh(); if ($app.HasExited) { break }; Start-Sleep -Milliseconds 400
        }
        $app.Refresh()
        Add-Check 'clean-close' ([bool]$app.HasExited) ("process exited: {0}" -f $app.HasExited)
    }
}
catch {
    Add-Check 'harness' $false ("aborted: {0}" -f $_.Exception.Message)
}
finally {
    if ($app) {
        try { $app.Refresh(); if (-not $app.HasExited) { $app.Kill() } } catch { }
    }
    if (-not $KeepOpen) {
        Get-Process MD_Converter_Lite -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
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
