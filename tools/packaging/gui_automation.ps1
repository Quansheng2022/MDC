#requires -Version 5.1
<#
.SYNOPSIS
    Shared UI-automation plumbing for the packaged MD Converter verification
    helpers (P12-08).

.DESCRIPTION
    Dot-source this file from a verification script:

        . "$PSScriptRoot\gui_automation.ps1"

    It provides the primitives needed to drive a *packaged* MD Converter GUI:

    * window discovery through Win32 enumeration (UI Automation does not list
      owned Qt dialogs under the desktop root);
    * real user actions delivered as window messages (Qt widgets do not honour
      the UI Automation InvokePattern here);
    * the native "common item dialog" input path;
    * the product's own conversion-slice helpers (select a file, run a
      conversion, read the terminal outcome) and DOCX artifact validation.

    Verification tooling only: nothing here changes product behaviour, and no
    conversion logic is reimplemented - every step is a real user action against
    the packaged application.
#>

$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

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

[void][MdcInput]::SetProcessDPIAware()

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

    public static List<IntPtr> AllHandles()
    {
        var handles = new List<IntPtr>();
        EnumWindows((hWnd, lParam) =>
        {
            if (IsWindowVisible(hWnd)) { handles.Add(hWnd); }
            return true;
        }, IntPtr.Zero);
        return handles;
    }

    public static List<IntPtr> AllHandlesIncludingHidden()
    {
        var handles = new List<IntPtr>();
        EnumWindows((hWnd, lParam) => { handles.Add(hWnd); return true; }, IntPtr.Zero);
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

$Global:Uia = [System.Windows.Automation.AutomationElement]
$Global:ControlType = [System.Windows.Automation.ControlType]
$Global:InvokePattern = [System.Windows.Automation.InvokePattern]
$Global:ValuePattern = [System.Windows.Automation.ValuePattern]
$Global:WindowPattern = [System.Windows.Automation.WindowPattern]
$Global:TogglePattern = [System.Windows.Automation.TogglePattern]

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

function Close-WindowElement {
    param([System.Windows.Automation.AutomationElement]$Element)
    $handle = [IntPtr]$Element.Current.NativeWindowHandle
    if ($handle -ne [IntPtr]::Zero) {
        [void][MdcInput]::PostMessage($handle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)  # WM_CLOSE
        return
    }
    $pattern = $Element.GetCurrentPattern($Global:WindowPattern::Pattern)
    $pattern.Close()
}

function Close-Dialog {
    param(
        [System.Windows.Automation.AutomationElement]$Dialog,
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

function Get-TextNames {
    param([System.Windows.Automation.AutomationElement]$Root)
    Get-Descendants -Root $Root |
        Where-Object { $_.Current.ControlType -eq $Global:ControlType::Text } |
        ForEach-Object { $_.Current.Name }
}

function Invoke-ButtonByName {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [string]$NamePattern,
        [int]$TimeoutSeconds = 10
    )
    $button = Find-Element -Root $Window -NamePattern $NamePattern -Type $Global:ControlType::Button -TimeoutSeconds $TimeoutSeconds
    if (-not $button) { return $false }
    if (-not $button.Current.IsEnabled) { return $false }
    Click-Element -Window $Window -Element $button
    return $true
}

function Select-SourceFile {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [int]$ProcessId,
        [string]$FilePath,
        [int]$TimeoutSeconds = 30
    )
    if (-not (Invoke-ButtonByName -Window $Window -NamePattern '^Select File$' -TimeoutSeconds $TimeoutSeconds)) {
        throw 'the Select File button was not found'
    }

    $dialog = Get-TopLevelWindow -ProcessId $ProcessId -ClassName '#32770' -TimeoutSeconds $TimeoutSeconds
    if (-not $dialog) { throw 'the native file dialog did not appear' }

    $dialogHandle = [IntPtr]$dialog.Current.NativeWindowHandle
    if (-not [MdcFileDialog]::SetFileName($dialogHandle, $FilePath)) {
        throw 'the file dialog has no file-name field'
    }
    Start-Sleep -Milliseconds 300
    if (-not [MdcFileDialog]::ClickButton($dialogHandle, 'Open')) {
        throw 'the file dialog has no Open button'
    }
    return (Wait-ForHandleGone -Handle $dialogHandle -TimeoutSeconds $TimeoutSeconds)
}

function Wait-ForConvertEnabled {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [int]$TimeoutSeconds = 30
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $candidate = Find-Element -Root $Window -NamePattern '^Convert$' -Type $Global:ControlType::Button -TimeoutSeconds 2
        if ($candidate -and $candidate.Current.IsEnabled) { return $candidate }
        Start-Sleep -Milliseconds 300
    }
    return $null
}

function Wait-ForConversionOutcome {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [int]$TimeoutSeconds = 900
    )
    # The status label exposes only its accessible name ("Status") to UI
    # Automation, so the terminal state is read from the product's own outcome
    # controls: Open Document / Open Folder are only actionable for a
    # successful result, while a visible Details... button marks a
    # warning/failure report.
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $openDocument = Find-Element -Root $Window -NamePattern '^Open Document$' -Type $Global:ControlType::Button -TimeoutSeconds 2
        if ($openDocument -and $openDocument.Current.IsEnabled) {
            return [ordered]@{
                outcome = 'SUCCESS'
                seconds = [math]::Round($stopwatch.Elapsed.TotalSeconds, 1)
                detail = 'Open Document / Open Folder enabled'
            }
        }
        $details = Find-Element -Root $Window -NamePattern '^Details' -Type $Global:ControlType::Button -TimeoutSeconds 1
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

function Convert-MarkdownThroughGui {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [int]$ProcessId,
        [string]$InputMarkdown,
        [int]$TimeoutSeconds = 900
    )
    $result = [ordered]@{
        selected = $false
        convert_enabled = $false
        outcome = $null
    }
    $result.selected = [bool](Select-SourceFile -Window $Window -ProcessId $ProcessId -FilePath $InputMarkdown)
    $convertButton = Wait-ForConvertEnabled -Window $Window
    $result.convert_enabled = [bool]$convertButton
    if ($convertButton) {
        Click-Element -Window $Window -Element $convertButton
        $result.outcome = Wait-ForConversionOutcome -Window $Window -TimeoutSeconds $TimeoutSeconds
    } else {
        $result.outcome = [ordered]@{ outcome = 'NOT_STARTED'; seconds = 0; detail = 'Convert never enabled' }
    }
    return $result
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

function Get-NewDocumentArtifacts {
    param([datetime]$Since, [string[]]$Roots)
    $found = New-Object System.Collections.ArrayList
    foreach ($root in $Roots) {
        if (-not $root -or -not (Test-Path -LiteralPath $root)) { continue }
        Get-ChildItem -LiteralPath $root -Filter '*.docx' -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -ge $Since } |
            ForEach-Object { [void]$found.Add($_.FullName) }
    }
    return @($found.ToArray() | Sort-Object -Unique)
}

function Get-AppWindowHandles {
    param([int]$ProcessId)
    return [MdcWindows]::Handles([uint32]$ProcessId)
}

function Get-DesktopWindowHandlesByClass {
    param([string]$ClassName)
    $handles = New-Object System.Collections.ArrayList
    foreach ($handle in [MdcWindows]::AllHandles()) {
        if ([MdcWindows]::ClassName($handle) -eq $ClassName) { [void]$handles.Add($handle) }
    }
    return @($handles.ToArray())
}

function Get-DesktopWindowsByClass {
    param(
        [Parameter(Mandatory = $true)][string]$ClassName,
        [switch]$IncludeHidden
    )
    $source = if ($IncludeHidden) {
        [MdcWindows]::AllHandlesIncludingHidden()
    } else {
        [MdcWindows]::AllHandles()
    }
    $items = New-Object System.Collections.ArrayList
    foreach ($handle in $source) {
        if ([MdcWindows]::ClassName($handle) -ne $ClassName) { continue }
        [void]$items.Add([ordered]@{
            handle = $handle
            title = [MdcWindows]::Title($handle)
        })
    }
    return @($items.ToArray())
}

function Wait-ForDesktopWindowByClass {
    param(
        [Parameter(Mandatory = $true)][string]$ClassName,
        [string]$TitleContains,
        [switch]$IncludeHidden,
        [int]$TimeoutSeconds = 60
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        foreach ($item in Get-DesktopWindowsByClass -ClassName $ClassName -IncludeHidden:$IncludeHidden) {
            if ($TitleContains -and $item.title -notlike "*$TitleContains*") { continue }
            return $item
        }
        Start-Sleep -Milliseconds 500
    }
    return $null
}

function Wait-ForDesktopWindowGone {
    param(
        [Parameter(Mandatory = $true)][string]$ClassName,
        [Parameter(Mandatory = $true)][string]$TitleContains,
        [int]$TimeoutSeconds = 30
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $remaining = @(Get-DesktopWindowsByClass -ClassName $ClassName -IncludeHidden |
            Where-Object { $_.title -like "*$TitleContains*" })
        if ($remaining.Count -eq 0) { return $true }
        Start-Sleep -Milliseconds 400
    }
    return $false
}

function Test-FileExclusivelyLocked {
    <#
        Return $true when another process holds the file open (Word reading the
        converted document is the behaviour this proves).
    #>
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    try {
        $stream = [System.IO.File]::Open($Path, 'Open', 'ReadWrite', 'None')
        $stream.Close()
        return $false
    } catch {
        return $true
    }
}
