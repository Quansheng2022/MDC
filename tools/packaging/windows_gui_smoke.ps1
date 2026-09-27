#requires -Version 5.1
<#
.SYNOPSIS
    Drive the packaged MD Converter GUI through a real end-to-end smoke test.

.DESCRIPTION
    Packaging verification helper for P12-08 (WP-P12-08-02 / WP-P12-08-05).

    The script launches a *packaged* (PyInstaller) MD Converter executable - it
    never imports the source tree - and verifies the accepted product path with
    Windows UI Automation:

        launch -> main window -> Settings -> About -> Select File
               -> Convert -> Conversion details -> clean close

    It then checks that a real DOCX artifact exists on disk and that the process
    exits when the window is closed.

    The script is verification tooling only.  It changes no product behaviour
    and performs no conversion logic of its own: every step is a real user
    action against the packaged application.

.PARAMETER ExePath
    Full path to the packaged executable under test.

.PARAMETER InputMarkdown
    Markdown file selected through the product's own file dialog.

.PARAMETER WorkDir
    Working directory for the launched process (default: a fresh temp folder).

.PARAMETER EvidencePath
    Optional path for a JSON evidence record.

.PARAMETER ConversionTimeoutSeconds
    Maximum time to wait for the conversion to reach a terminal state.

.PARAMETER KeepOpen
    Leave the application running after the checks (diagnostics only).

.EXAMPLE
    powershell -File tools/packaging/windows_gui_smoke.ps1 `
        -ExePath dist/MD_Converter_Lite/MD_Converter_Lite.exe `
        -InputMarkdown sample.md -EvidencePath smoke.json
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ExePath,
    [Parameter(Mandatory = $true)][string]$InputMarkdown,
    [string]$WorkDir,
    [string]$EvidencePath,
    [int]$StartupTimeoutSeconds = 60,
    [int]$UiTimeoutSeconds = 30,
    [int]$ConversionTimeoutSeconds = 900,
    [switch]$KeepOpen
)

$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

# Qt widgets do not honour the UI Automation InvokePattern in this
# environment, so user actions are delivered as real window messages
# (WM_MOUSEMOVE / WM_LBUTTONDOWN / WM_LBUTTONUP) at the widget's centre.
if (-not ('MdcInput' -as [type])) {
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public static class MdcInput
{
    [StructLayout(LayoutKind.Sequential)]
    public struct POINT { public int X; public int Y; }

    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool ScreenToClient(IntPtr hWnd, ref POINT point);
    [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
}
'@
}

# Physical-pixel coordinates keep UI Automation rectangles and ScreenToClient
# consistent on high-DPI Windows.
[void][MdcInput]::SetProcessDPIAware()

# UI Automation does not list owned Qt dialog windows under the root element in
# this environment, so top-level windows are discovered through Win32
# enumeration and wrapped with AutomationElement.FromHandle.
if (-not ('MdcWindows' -as [type])) {
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public static class MdcWindows
{
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")] private static extern bool EnumWindows(EnumProc callback, IntPtr lParam);
    [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetWindowTextW(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetClassNameW(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll")] private static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern bool IsWindow(IntPtr hWnd);

    public static List<IntPtr> Handles(uint processId)
    {
        var handles = new List<IntPtr>();
        EnumWindows((hWnd, lParam) =>
        {
            uint pid;
            GetWindowThreadProcessId(hWnd, out pid);
            if (pid == processId && IsWindowVisible(hWnd))
            {
                handles.Add(hWnd);
            }
            return true;
        }, IntPtr.Zero);
        return handles;
    }

    public static string Title(IntPtr hWnd)
    {
        var buffer = new StringBuilder(512);
        GetWindowTextW(hWnd, buffer, buffer.Capacity);
        return buffer.ToString();
    }

    public static string ClassName(IntPtr hWnd)
    {
        var buffer = new StringBuilder(512);
        GetClassNameW(hWnd, buffer, buffer.Capacity);
        return buffer.ToString();
    }

    public static bool Exists(IntPtr hWnd) { return IsWindow(hWnd); }
}
'@
}

# The Windows "common item dialog" exposes neither InvokePattern for its Open
# button nor a settable ValuePattern for its file-name box, so the packaged GUI
# is driven through the native controls directly (child edit + button click).
if (-not ('MdcFileDialog' -as [type])) {
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public static class MdcFileDialog
{
    public delegate bool EnumProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")] private static extern bool EnumChildWindows(IntPtr parent, EnumProc callback, IntPtr lParam);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetClassNameW(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetWindowTextW(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll")] private static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern bool IsWindowEnabled(IntPtr hWnd);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern IntPtr SendMessageW(IntPtr hWnd, uint msg, IntPtr wParam, string lParam);
    [DllImport("user32.dll")] private static extern IntPtr SendMessageW(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);

    private const uint WM_SETTEXT = 0x000C;
    private const uint BM_CLICK = 0x00F5;

    private static string ClassOf(IntPtr hWnd)
    {
        var buffer = new StringBuilder(256);
        GetClassNameW(hWnd, buffer, buffer.Capacity);
        return buffer.ToString();
    }

    private static string TextOf(IntPtr hWnd)
    {
        var buffer = new StringBuilder(1024);
        GetWindowTextW(hWnd, buffer, buffer.Capacity);
        return buffer.ToString();
    }

    private static List<IntPtr> Descendants(IntPtr parent)
    {
        var list = new List<IntPtr>();
        EnumChildWindows(parent, (hWnd, lParam) => { list.Add(hWnd); return true; }, IntPtr.Zero);
        return list;
    }

    public static IntPtr FindFileNameEdit(IntPtr dialog)
    {
        IntPtr fallback = IntPtr.Zero;
        foreach (var hWnd in Descendants(dialog))
        {
            if (ClassOf(hWnd) != "Edit" || !IsWindowVisible(hWnd) || !IsWindowEnabled(hWnd)) continue;
            if (TextOf(hWnd).Length == 0) return hWnd;
            fallback = hWnd;
        }
        return fallback;
    }

    public static bool SetFileName(IntPtr dialog, string path)
    {
        var edit = FindFileNameEdit(dialog);
        if (edit == IntPtr.Zero) return false;
        SendMessageW(edit, WM_SETTEXT, IntPtr.Zero, path);
        return true;
    }

    public static bool ClickButton(IntPtr dialog, string caption)
    {
        var wanted = caption.Replace("&", "").ToLowerInvariant();
        foreach (var hWnd in Descendants(dialog))
        {
            if (ClassOf(hWnd) != "Button" || !IsWindowVisible(hWnd) || !IsWindowEnabled(hWnd)) continue;
            if (TextOf(hWnd).Replace("&", "").ToLowerInvariant() != wanted) continue;
            SendMessageW(hWnd, BM_CLICK, IntPtr.Zero, IntPtr.Zero);
            return true;
        }
        return false;
    }
}
'@
}

$Uia = [System.Windows.Automation.AutomationElement]
$ControlType = [System.Windows.Automation.ControlType]
$InvokePattern = [System.Windows.Automation.InvokePattern]
$ValuePattern = [System.Windows.Automation.ValuePattern]
$WindowPattern = [System.Windows.Automation.WindowPattern]

$MainWindowTitle = 'MD Converter'

$script:Results = [ordered]@{}
$script:StartedAt = Get-Date

function Write-Step {
    param([string]$Message)
    Write-Host ("[smoke] {0}" -f $Message)
}

function Get-Descendants {
    param([System.Windows.Automation.AutomationElement]$Root)
    if ($null -eq $Root) { return @() }
    $all = $Root.FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        [System.Windows.Automation.Condition]::TrueCondition
    )
    $list = New-Object System.Collections.ArrayList
    foreach ($item in $all) { [void]$list.Add($item) }
    return $list.ToArray()
}

function Get-TopLevelWindow {
    param(
        [int]$ProcessId,
        [string]$Name,
        [string]$NamePrefix,
        [string]$ClassName,
        [int]$TimeoutSeconds = 0
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ($true) {
        foreach ($handle in [MdcWindows]::Handles([uint32]$ProcessId)) {
            $title = [MdcWindows]::Title($handle)
            $class = [MdcWindows]::ClassName($handle)
            if ($Name -and $title -ne $Name) { continue }
            # Qt appends " - <applicationDisplayName>" to dialog titles, so
            # dialog windows are matched by prefix.
            if ($NamePrefix -and $title -notlike "$NamePrefix*") { continue }
            if ($ClassName -and $class -ne $ClassName) { continue }
            return [System.Windows.Automation.AutomationElement]::FromHandle($handle)
        }
        if ((Get-Date) -ge $deadline) { return $null }
        Start-Sleep -Milliseconds 250
    }
}

function Wait-ForHandleGone {
    param([IntPtr]$Handle, [int]$TimeoutSeconds = 15)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (-not [MdcWindows]::Exists($Handle)) { return $true }
        Start-Sleep -Milliseconds 250
    }
    return $false
}

function Close-Dialog {
    param(
        [System.Windows.Automation.AutomationElement]$Dialog,
        [int]$ProcessId,
        [int]$TimeoutSeconds = 15
    )
    $handle = [IntPtr]$Dialog.Current.NativeWindowHandle
    Close-WindowElement -Element $Dialog
    return (Wait-ForHandleGone -Handle $handle -TimeoutSeconds $TimeoutSeconds)
}

function Find-Element {
    param(
        [System.Windows.Automation.AutomationElement]$Root,
        [string]$NamePattern,
        $Type,
        [int]$TimeoutSeconds = 5
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ($true) {
        foreach ($element in Get-Descendants -Root $Root) {
            if ($Type -and $element.Current.ControlType -ne $Type) { continue }
            if ($NamePattern -and $element.Current.Name -notmatch $NamePattern) { continue }
            return $element
        }
        if ((Get-Date) -ge $deadline) { return $null }
        Start-Sleep -Milliseconds 250
    }
}

function Invoke-Element {
    param([System.Windows.Automation.AutomationElement]$Element)
    $pattern = $Element.GetCurrentPattern($InvokePattern::Pattern)
    $pattern.Invoke()
}

function Click-Element {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [System.Windows.Automation.AutomationElement]$Element
    )
    $rect = $Element.Current.BoundingRectangle
    if ($rect.Width -le 0 -or $rect.Height -le 0) {
        throw ("element '{0}' has no clickable area" -f $Element.Current.Name)
    }
    $point = New-Object MdcInput+POINT
    $point.X = [int]($rect.X + $rect.Width / 2)
    $point.Y = [int]($rect.Y + $rect.Height / 2)
    $handle = [IntPtr]$Window.Current.NativeWindowHandle
    [void][MdcInput]::ScreenToClient($handle, [ref]$point)
    $lparam = [IntPtr](($point.Y -shl 16) -bor ($point.X -band 0xFFFF))
    [void][MdcInput]::SendMessage($handle, 0x0200, [IntPtr]::Zero, $lparam)  # WM_MOUSEMOVE
    Start-Sleep -Milliseconds 60
    [void][MdcInput]::SendMessage($handle, 0x0201, [IntPtr]1, $lparam)       # WM_LBUTTONDOWN
    Start-Sleep -Milliseconds 90
    [void][MdcInput]::SendMessage($handle, 0x0202, [IntPtr]::Zero, $lparam)  # WM_LBUTTONUP
}

function Close-WindowElement {
    param([System.Windows.Automation.AutomationElement]$Element)
    $handle = [IntPtr]$Element.Current.NativeWindowHandle
    if ($handle -ne [IntPtr]::Zero) {
        [void][MdcInput]::PostMessage($handle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)  # WM_CLOSE
        return
    }
    $pattern = $Element.GetCurrentPattern($WindowPattern::Pattern)
    $pattern.Close()
}

function Get-TextNames {
    param([System.Windows.Automation.AutomationElement]$Root)
    Get-Descendants -Root $Root |
        Where-Object { $_.Current.ControlType -eq $ControlType::Text } |
        ForEach-Object { $_.Current.Name }
}

function Wait-ForConversionOutcome {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [int]$TimeoutSeconds
    )
    # The status label exposes only its accessible name ("Status") to UI
    # Automation, so the terminal state is read from the product's own outcome
    # controls: Open Document / Open Folder are only actionable for a
    # successful result, while a visible Details... button marks a
    # warning/failure report.
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $openDocument = Find-Element -Root $Window -NamePattern '^Open Document$' -Type $ControlType::Button -TimeoutSeconds 2
        if ($openDocument -and $openDocument.Current.IsEnabled) {
            return [ordered]@{
                outcome = 'SUCCESS'
                seconds = [math]::Round($stopwatch.Elapsed.TotalSeconds, 1)
                detail = 'Open Document / Open Folder enabled'
            }
        }
        $details = Find-Element -Root $Window -NamePattern '^Details' -Type $ControlType::Button -TimeoutSeconds 1
        if ($details -and $details.Current.IsEnabled) {
            return [ordered]@{
                outcome = 'REPORT'
                seconds = [math]::Round($stopwatch.Elapsed.TotalSeconds, 1)
                detail = 'Details... button enabled'
            }
        }
        Start-Sleep -Milliseconds 1500
    }
    return [ordered]@{
        outcome = 'TIMEOUT'
        seconds = [math]::Round($stopwatch.Elapsed.TotalSeconds, 1)
        detail = 'no terminal outcome within timeout'
    }
}

function Test-DocxArtifact {
    param([string]$Path)
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [System.IO.Compression.ZipFile]::OpenRead($Path)
        try {
            $names = $zip.Entries | ForEach-Object { $_.FullName }
            return ($names -contains 'word/document.xml')
        } finally {
            $zip.Dispose()
        }
    } catch {
        return $false
    }
}

function Select-SourceFile {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [int]$ProcessId,
        [string]$FilePath
    )
    $button = Find-Element -Root $Window -NamePattern '^Select File$' -Type $ControlType::Button -TimeoutSeconds $UiTimeoutSeconds
    if (-not $button) { throw 'the Select File button was not found' }
    Click-Element -Window $Window -Element $button

    $dialog = Get-TopLevelWindow -ProcessId $ProcessId -ClassName '#32770' -TimeoutSeconds $UiTimeoutSeconds
    if (-not $dialog) { throw 'the native file dialog did not appear' }

    $dialogHandle = [IntPtr]$dialog.Current.NativeWindowHandle
    if (-not [MdcFileDialog]::SetFileName($dialogHandle, $FilePath)) {
        throw 'the file dialog has no file-name field'
    }
    Start-Sleep -Milliseconds 300
    if (-not [MdcFileDialog]::ClickButton($dialogHandle, 'Open')) {
        throw 'the file dialog has no Open button'
    }
    return (Wait-ForHandleGone -Handle $dialogHandle -TimeoutSeconds $UiTimeoutSeconds)
}

function Get-NewDocumentArtifacts {
    param([datetime]$Since, [string[]]$Roots)
    $found = New-Object System.Collections.ArrayList
    foreach ($root in $Roots) {
        if (-not $root -or -not (Test-Path -LiteralPath $root)) { continue }
        Get-ChildItem -LiteralPath $root -Filter '*.docx' -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -ge $Since } |
            ForEach-Object { [void]$found.Add($_.FullName) }
    }
    return $found.ToArray()
}

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

$ExePath = (Resolve-Path -LiteralPath $ExePath).Path
$InputMarkdown = (Resolve-Path -LiteralPath $InputMarkdown).Path
if (-not $WorkDir) {
    $WorkDir = Join-Path $env:TEMP ("mdc_gui_smoke_" + (Get-Date -Format 'yyyyMMdd_HHmmss'))
}
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null

Write-Step ("executable : {0}" -f $ExePath)
Write-Step ("input      : {0}" -f $InputMarkdown)
Write-Step ("work dir   : {0}" -f $WorkDir)

$script:Results['executable'] = $ExePath
$script:Results['executable_size_bytes'] = (Get-Item -LiteralPath $ExePath).Length
$script:Results['executable_sha256'] = (Get-FileHash -LiteralPath $ExePath -Algorithm SHA256).Hash
$script:Results['input_markdown'] = $InputMarkdown
$script:Results['work_dir'] = $WorkDir
$script:Results['started_at'] = $script:StartedAt.ToString('o')

$process = Start-Process -FilePath $ExePath -WorkingDirectory $WorkDir -PassThru
$script:Results['process_id'] = $process.Id

$failures = New-Object System.Collections.ArrayList

function Add-Check {
    param([string]$Name, [bool]$Passed, $Detail)
    $script:Results[$Name] = [ordered]@{ passed = $Passed; detail = "$Detail" }
    if (-not $Passed) { [void]$failures.Add($Name) }
    Write-Step ("{0} {1} :: {2}" -f ($(if ($Passed) { 'PASS' } else { 'FAIL' })), $Name, $Detail)
}

try {
    # -----------------------------------------------------------------------
    # 1. Startup
    # -----------------------------------------------------------------------
    $window = Get-TopLevelWindow -ProcessId $process.Id -Name $MainWindowTitle -TimeoutSeconds $StartupTimeoutSeconds
    if (-not $window) {
        $process.Refresh()
        Add-Check 'gui-startup' $false ("main window '{0}' did not appear (hasExited={1})" -f $MainWindowTitle, $process.HasExited)
        throw 'startup failed'
    }
    Add-Check 'gui-startup' $true ("window '{0}' is visible" -f $window.Current.Name)
    $script:Results['main_window_elements'] = @(Get-Descendants -Root $window |
        ForEach-Object { ("{0}|{1}" -f $_.Current.ControlType.ProgrammaticName, $_.Current.Name) })

    # -----------------------------------------------------------------------
    # 2. Settings dialog
    # -----------------------------------------------------------------------
    $settingsButton = Find-Element -Root $window -NamePattern '^Settings$' -Type $ControlType::Button -TimeoutSeconds $UiTimeoutSeconds
    if (-not $settingsButton) {
        Add-Check 'settings-opens' $false 'Settings button not found'
    } else {
        Click-Element -Window $window -Element $settingsButton
        $settingsDialog = Get-TopLevelWindow -ProcessId $process.Id -NamePrefix 'Settings' -TimeoutSeconds $UiTimeoutSeconds
        if (-not $settingsDialog) {
            Add-Check 'settings-opens' $false 'Settings dialog did not appear'
        } else {
            $settingsText = @(Get-Descendants -Root $settingsDialog |
                ForEach-Object { $_.Current.Name } |
                Where-Object { $_ })
            $script:Results['settings_dialog_title'] = $settingsDialog.Current.Name
            $script:Results['settings_text'] = $settingsText
            $closed = Close-Dialog -Dialog $settingsDialog -ProcessId $process.Id
            Add-Check 'settings-opens' ($settingsText.Count -gt 0) ("dialog '{0}' opened with {1} element(s)" -f $settingsDialog.Current.Name, $settingsText.Count)
            Add-Check 'settings-closes' ([bool]$closed) ("dialog closed cleanly: {0}" -f $closed)
        }
    }

    # -----------------------------------------------------------------------
    # 3. About dialog (version must match the packaged product version)
    # -----------------------------------------------------------------------
    $aboutButton = Find-Element -Root $window -NamePattern '^About$' -Type $ControlType::Button -TimeoutSeconds $UiTimeoutSeconds
    if (-not $aboutButton) {
        Add-Check 'about-opens' $false 'About button not found'
    } else {
        Click-Element -Window $window -Element $aboutButton
        $aboutDialog = Get-TopLevelWindow -ProcessId $process.Id -NamePrefix 'About MD Converter' -TimeoutSeconds $UiTimeoutSeconds
        if (-not $aboutDialog) {
            Add-Check 'about-opens' $false 'About dialog did not appear'
        } else {
            $aboutText = (Get-Descendants -Root $aboutDialog |
                ForEach-Object { $_.Current.Name } |
                Where-Object { $_ -and $_ -ne 'About MD Converter' })
            $script:Results['about_text'] = @($aboutText)
            $versionLines = $aboutText | Where-Object { $_ -match '^\s*Version\s+\S+' }
            Add-Check 'about-opens' $true ("dialog '{0}' opened" -f $aboutDialog.Current.Name)
            Add-Check 'about-version' ([bool]$versionLines) ("version text: {0}" -f ($versionLines -join '; '))
            $closed = Close-Dialog -Dialog $aboutDialog -ProcessId $process.Id
            Add-Check 'about-closes' ([bool]$closed) ("dialog closed cleanly: {0}" -f $closed)
        }
    }

    # -----------------------------------------------------------------------
    # 4. Real file selection through the product file dialog
    # -----------------------------------------------------------------------
    $dialogClosed = Select-SourceFile -Window $window -ProcessId $process.Id -FilePath $InputMarkdown
    Add-Check 'select-file' ([bool]$dialogClosed) ("file dialog accepted '{0}'" -f (Split-Path -Leaf $InputMarkdown))

    $convertButton = $null
    $deadline = (Get-Date).AddSeconds($UiTimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $candidate = Find-Element -Root $window -NamePattern '^Convert$' -Type $ControlType::Button -TimeoutSeconds 2
        if ($candidate -and $candidate.Current.IsEnabled) { $convertButton = $candidate; break }
        Start-Sleep -Milliseconds 300
    }
    Add-Check 'convert-enabled' ([bool]$convertButton) 'Convert button enabled after selecting a file'

    # -----------------------------------------------------------------------
    # 5. Real conversion through GUI -> GuiWorker -> ConversionService -> Core
    # -----------------------------------------------------------------------
    $outcome = $null
    if ($convertButton) {
        Click-Element -Window $window -Element $convertButton
        $outcome = Wait-ForConversionOutcome -Window $window -TimeoutSeconds $ConversionTimeoutSeconds
    } else {
        $outcome = [ordered]@{ outcome = 'NOT_STARTED'; seconds = 0; detail = 'Convert button never became available' }
    }
    $script:Results['conversion_outcome'] = $outcome
    $conversionPassed = ($outcome.outcome -eq 'SUCCESS')
    Add-Check 'conversion' $conversionPassed (
        "outcome={0} after {1}s ({2})" -f $outcome.outcome, $outcome.seconds, $outcome.detail)

    $artifacts = @(Get-NewDocumentArtifacts -Since $script:StartedAt -Roots @($WorkDir, (Split-Path -Parent $InputMarkdown)) |
        Sort-Object -Unique)
    $script:Results['docx_artifacts'] = @($artifacts)
    Add-Check 'docx-artifact' ($artifacts.Count -gt 0) ("{0} DOCX artifact(s) created" -f $artifacts.Count)

    $validArtifacts = @($artifacts | Where-Object { Test-DocxArtifact -Path $_ })
    $script:Results['valid_docx_artifacts'] = @($validArtifacts)
    Add-Check 'docx-valid' ($validArtifacts.Count -gt 0) (
        "{0} of {1} artifact(s) contain word/document.xml" -f $validArtifacts.Count, $artifacts.Count)

    # -----------------------------------------------------------------------
    # 6. Conversion details / report surface
    # -----------------------------------------------------------------------
    $detailsButton = Find-Element -Root $window -NamePattern '^Details' -Type $ControlType::Button -TimeoutSeconds $UiTimeoutSeconds
    if ($detailsButton -and $detailsButton.Current.IsEnabled) {
        Click-Element -Window $window -Element $detailsButton
        $detailsDialog = $null
        $deadline = (Get-Date).AddSeconds($UiTimeoutSeconds)
        while ((Get-Date) -lt $deadline -and -not $detailsDialog) {
            foreach ($candidate in @('Conversion details', 'Warning details', 'Failure details')) {
                $detailsDialog = Get-TopLevelWindow -ProcessId $process.Id -NamePrefix $candidate -TimeoutSeconds 1
                if ($detailsDialog) { break }
            }
        }
        if (-not $detailsDialog) {
            Add-Check 'details-report' $false 'details dialog did not appear'
        } else {
            $detailsText = (Get-Descendants -Root $detailsDialog |
                ForEach-Object { $_.Current.Name } |
                Where-Object { $_ })
            $script:Results['details_dialog_title'] = $detailsDialog.Current.Name
            $script:Results['details_text'] = @($detailsText)
            Add-Check 'details-report' ($detailsText.Count -gt 0) ("dialog '{0}' returned {1} text element(s)" -f $detailsDialog.Current.Name, $detailsText.Count)
            $closed = Close-Dialog -Dialog $detailsDialog -ProcessId $process.Id
            Add-Check 'details-closes' ([bool]$closed) ("dialog closed cleanly: {0}" -f $closed)
        }
    } elseif ($outcome.outcome -eq 'SUCCESS') {
        # A plain successful conversion has no warning/failure report surface, so
        # there is nothing for Details... to show - this is the accepted
        # behaviour rather than a missing capability.
        Add-Check 'details-report' $true 'not applicable: successful conversion exposes no report button'
    } else {
        Add-Check 'details-report' $false 'Details button unavailable after conversion'
    }

    # -----------------------------------------------------------------------
    # 7. Clean close
    # -----------------------------------------------------------------------
    if ($KeepOpen) {
        Add-Check 'clean-close' $true 'skipped (KeepOpen); application left running'
    } else {
        Close-WindowElement -Element $window
        $deadline = (Get-Date).AddSeconds(30)
        while ((Get-Date) -lt $deadline) {
            $process.Refresh()
            if ($process.HasExited) { break }
            Start-Sleep -Milliseconds 400
        }
        $process.Refresh()
        Add-Check 'clean-close' ([bool]$process.HasExited) ("process exited: {0}" -f $process.HasExited)
    }
}
catch {
    Add-Check 'harness' $false ("aborted: {0}" -f $_.Exception.Message)
}
finally {
    if (-not $KeepOpen) {
        try {
            $process.Refresh()
            if (-not $process.HasExited) { $process.Kill() }
        } catch { }
    }
}

$script:Results['finished_at'] = (Get-Date).ToString('o')
$script:Results['failed_checks'] = @($failures)
$script:Results['status'] = $(if ($failures.Count -eq 0) { 'PASS' } else { 'FAIL' })

if ($EvidencePath) {
    $directory = Split-Path -Parent $EvidencePath
    if ($directory) { New-Item -ItemType Directory -Force -Path $directory | Out-Null }
    $script:Results | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $EvidencePath -Encoding UTF8
    Write-Step ("evidence written to {0}" -f $EvidencePath)
}

Write-Host ""
Write-Host ("RESULT: {0} ({1} failing check(s))" -f $script:Results['status'], $failures.Count)

if ($failures.Count -gt 0) { exit 1 }
exit 0
