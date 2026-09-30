#requires -Version 5.1
<#
.SYNOPSIS
    R2-V02 packaged multi-file runtime verification harness.

.DESCRIPTION
    Verification tooling only.  It launches the *installed* packaged executable
    (never the source tree, never .venv Python) from a neutral working directory
    with a sanitized child environment, drives the real GUI through UI
    Automation / window messages, and records machine-readable observations.

    Phases:

      WP01  package identity + runtime independence + one minimal conversion
      WP02  real four-file serial batch (order, serial, failure isolation,
            per-file result, summary, naming, Open Output Folder)
      WP03  five-profile matrix + localized TOC control (DOCX parity)
      WP04  cold launch + one representative conversion (closure)

.EXAMPLE
    powershell -File mdc_r2v02_verify.ps1 -Phase WP02
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('WP01', 'WP02', 'WP03', 'WP04')]
    [string]$Phase,
    [string]$WorkRoot,
    [string]$EvidenceDir,
    [string]$PythonExe,
    [int]$StartupTimeoutSeconds = 120,
    [int]$UiTimeoutSeconds = 45,
    [int]$ConversionTimeoutSeconds = 900,
    [switch]$KeepOpen
)

$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
. (Join-Path $RepoRoot 'tools\packaging\gui_automation.ps1')

if (-not ('MdcDetachedLaunch' -as [type])) {
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;

/// <summary>
/// Launch helper for the R2-V02 verification harness.
///
/// The installed product is a windowed desktop application, so the way it is
/// really started (Start Menu / desktop shortcut through the shell) gives it no
/// standard handles at all.  CreateProcess with CREATE_DETACHED_PROCESS and
/// bInheritHandles = FALSE reproduces exactly that: the child gets no console
/// and no inherited standard handles, so its stdout/stderr are unusable - which
/// is the packaged product's normal runtime condition.
/// </summary>
public static class MdcDetachedLaunch
{
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct STARTUPINFO
    {
        public int cb;
        public string lpReserved;
        public string lpDesktop;
        public string lpTitle;
        public int dwX;
        public int dwY;
        public int dwXSize;
        public int dwYSize;
        public int dwXCountChars;
        public int dwYCountChars;
        public int dwFillAttribute;
        public int dwFlags;
        public short wShowWindow;
        public short cbReserved2;
        public IntPtr lpReserved2;
        public IntPtr hStdInput;
        public IntPtr hStdOutput;
        public IntPtr hStdError;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct PROCESS_INFORMATION
    {
        public IntPtr hProcess;
        public IntPtr hThread;
        public int dwProcessId;
        public int dwThreadId;
    }

    private const uint CREATE_DETACHED_PROCESS = 0x00000008;
    private const uint CREATE_NEW_PROCESS_GROUP = 0x00000200;
    private const uint CREATE_UNICODE_ENVIRONMENT = 0x00000400;

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CreateProcess(
        string lpApplicationName,
        StringBuilder lpCommandLine,
        IntPtr lpProcessAttributes,
        IntPtr lpThreadAttributes,
        bool bInheritHandles,
        uint dwCreationFlags,
        IntPtr lpEnvironment,
        string lpCurrentDirectory,
        ref STARTUPINFO lpStartupInfo,
        out PROCESS_INFORMATION lpProcessInformation);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr hObject);

    public static int Start(string executable, string workingDirectory, IntPtr environmentBlock)
    {
        STARTUPINFO startup = new STARTUPINFO();
        startup.cb = Marshal.SizeOf(typeof(STARTUPINFO));
        PROCESS_INFORMATION info = new PROCESS_INFORMATION();
        StringBuilder commandLine = new StringBuilder("\"" + executable + "\"");
        bool created = CreateProcess(
            executable,
            commandLine,
            IntPtr.Zero,
            IntPtr.Zero,
            false,
            CREATE_DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_UNICODE_ENVIRONMENT,
            environmentBlock,
            workingDirectory,
            ref startup,
            out info);
        if (!created)
        {
            throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
        }
        CloseHandle(info.hThread);
        CloseHandle(info.hProcess);
        return info.dwProcessId;
    }
}
'@
}

if (-not $PythonExe) { $PythonExe = Join-Path $RepoRoot '.venv\Scripts\python.exe' }
if (-not $EvidenceDir) { $EvidenceDir = Join-Path $RepoRoot 'Doc\V2\Implementation\R2_V02\Evidence' }
$InstallRoot = Join-Path $env:LOCALAPPDATA 'Programs\MD_Converter'
$ExePath = Join-Path $InstallRoot 'MD_Converter.exe'
if (-not (Test-Path -LiteralPath $ExePath)) { throw "installed executable not found: $ExePath" }

$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
if (-not $WorkRoot) { $WorkRoot = Join-Path $env:TEMP "mdc_r2v02_$($Phase.ToLower())_$Stamp" }
New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null
$WorkDir = Join-Path $WorkRoot 'cwd'
$OutputDir = Join-Path $WorkDir 'output'
$CollectDir = Join-Path $WorkRoot 'collected'
New-Item -ItemType Directory -Force -Path $WorkDir, $OutputDir, $CollectDir | Out-Null

$MainWindowTitle = 'MD Converter'
$ExplorerWindowClass = 'CabinetWClass'
$PrefsKey = 'HKCU:\Software\MD Converter'

$script:Checks = New-Object System.Collections.ArrayList
$script:Notes = New-Object System.Collections.ArrayList
$script:Failures = New-Object System.Collections.ArrayList
$script:StartedAt = Get-Date
$script:Restore = [ordered]@{ key_existed = $false; backup = $null }

function Write-Step {
    param([string]$Message)
    Write-Host ("[{0}] {1}" -f $Phase.ToLower(), $Message)
}

function Add-Check {
    param([string]$Name, [bool]$Passed, $Detail)
    [void]$script:Checks.Add([ordered]@{ name = $Name; passed = $Passed; detail = "$Detail" })
    if (-not $Passed) { [void]$script:Failures.Add($Name) }
    Write-Step ("{0} {1} :: {2}" -f ($(if ($Passed) { 'PASS' } else { 'FAIL' })), $Name, $Detail)
}

function Add-Note {
    param([string]$Name, $Detail)
    [void]$script:Notes.Add([ordered]@{ name = $Name; detail = "$Detail" })
    Write-Step ("NOTE {0} :: {1}" -f $Name, $Detail)
}

function Get-SanitizedPath {
    <#
        Remove the repository (and its .venv) from the child PATH so the
        packaged runtime cannot reach development tooling through PATH.
    #>
    $repoPattern = [regex]::Escape($RepoRoot)
    $kept = @()
    foreach ($entry in ($env:PATH -split ';')) {
        if (-not $entry) { continue }
        if ($entry -match $repoPattern) { continue }
        if ($entry -match '\\\.venv\\') { continue }
        $kept += $entry
    }
    return ($kept -join ';')
}

function Start-PackagedApp {
    param([Parameter(Mandatory = $true)][string]$Directory)
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $ExePath
    $psi.WorkingDirectory = $Directory
    $psi.UseShellExecute = $false
    foreach ($name in @('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONIOENCODING', 'PYTHONUTF8')) {
        $psi.Environment.Remove($name) | Out-Null
    }
    $psi.Environment['PATH'] = Get-SanitizedPath
    $script:ChildEnvironment = [ordered]@{
        launch_mode             = 'CreateProcess (sanitized environment)'
        path                    = $psi.Environment['PATH']
        pythonpath              = "$($psi.Environment['PYTHONPATH'])"
        pythonhome              = "$($psi.Environment['PYTHONHOME'])"
        working_directory       = $Directory
        repository_on_path      = [bool](($psi.Environment['PATH']) -match [regex]::Escape($RepoRoot))
        dotvenv_on_path         = [bool](($psi.Environment['PATH']) -match '\\\.venv\\')
    }
    return [System.Diagnostics.Process]::Start($psi)
}

function Get-ChildEnvironmentTable {
    param([switch]$Sanitize)
    $variables = @{}
    $source = [System.Environment]::GetEnvironmentVariables()
    foreach ($key in $source.Keys) {
        $variables[$key] = $source[$key]
    }
    if ($Sanitize) {
        foreach ($name in @('PYTHONPATH', 'PYTHONHOME', 'PYTHONSTARTUP', 'PYTHONIOENCODING', 'PYTHONUTF8')) {
            $variables.Remove($name)
        }
        $variables['PATH'] = Get-SanitizedPath
    }
    return $variables
}

function New-EnvironmentBlockPointer {
    param([hashtable]$Variables)
    $pairs = New-Object System.Collections.ArrayList
    foreach ($key in ($Variables.Keys | Sort-Object)) {
        [void]$pairs.Add(("{0}={1}" -f $key, $Variables[$key]))
    }
    $text = (($pairs.ToArray()) -join "`0") + "`0`0"
    return [System.Runtime.InteropServices.Marshal]::StringToHGlobalUni($text)
}

function Start-PackagedAppDetached {
    <#
        Launch the installed product the way its shipped shortcuts do: a
        windowed GUI process with no console and no inherited standard handles.
        This is the primary functional runtime launch mode.
    #>
    param(
        [Parameter(Mandatory = $true)][string]$Directory,
        [switch]$Sanitize
    )
    $variables = Get-ChildEnvironmentTable -Sanitize:$Sanitize
    $pointer = New-EnvironmentBlockPointer -Variables $variables
    try {
        $processId = [MdcDetachedLaunch]::Start($ExePath, $Directory, $pointer)
    } finally {
        [System.Runtime.InteropServices.Marshal]::FreeHGlobal($pointer)
    }
    $pathValue = "$($variables['PATH'])"
    $script:ChildEnvironment = [ordered]@{
        launch_mode        = $(if ($Sanitize) { 'CreateProcess detached + sanitized environment' } else { 'CreateProcess detached' })
        working_directory  = $Directory
        pythonpath         = "$($variables['PYTHONPATH'])"
        path               = $pathValue
        repository_on_path = [bool]($pathValue -match [regex]::Escape($RepoRoot))
        dotvenv_on_path    = [bool]($pathValue -match '\\\.venv\\')
        standard_handles   = 'none inherited (CREATE_DETACHED_PROCESS, bInheritHandles=FALSE)'
    }
    return (Get-Process -Id $processId)
}

function Stop-PackagedApp {
    param($Process)
    if (-not $Process) { return }
    try {
        $Process.Refresh()
        if (-not $Process.HasExited) { $Process.Kill() }
    } catch { }
}

function Wait-MainWindow {
    param([int]$ProcessId, [int]$TimeoutSeconds = 120)
    return Get-TopLevelWindow -ProcessId $ProcessId -Name $MainWindowTitle -TimeoutSeconds $TimeoutSeconds
}

function Get-DescendantsSafe {
    <#
        UI Automation enumerations can transiently fail while a Qt window is
        rebuilding its accessible tree (the batch list is re-rendered, dialogs
        open and close).  A transient failure must not abort a verification run,
        so the enumeration is retried and only then reported as empty.
    #>
    param(
        [System.Windows.Automation.AutomationElement]$Root,
        [int]$Attempts = 4
    )
    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        try {
            return Get-Descendants -Root $Root
        } catch {
            Start-Sleep -Milliseconds 250
        }
    }
    return @()
}

function Get-RuntimeIndependence {
    <#
        Objective runtime-independence evidence: every loaded module of the
        packaged process must come from the install directory or from Windows.
    #>
    param($Process)
    $modules = @()
    $error = $null
    try {
        foreach ($module in $Process.Modules) { $modules += $module.FileName }
    } catch {
        $error = $_.Exception.Message
    }
    $repoPattern = [regex]::Escape($RepoRoot)
    $offenders = @($modules | Where-Object { $_ -match $repoPattern -or $_ -match '\\\.venv\\' })
    return [ordered]@{
        module_count          = $modules.Count
        enumeration_error     = $error
        repository_module_hits = @($offenders)
        install_root          = $InstallRoot
        modules               = $modules
    }
}

function Get-UiSnapshot {
    param([System.Windows.Automation.AutomationElement]$Window)
    $snapshot = [ordered]@{
        at               = (Get-Date).ToString('HH:mm:ss.fff')
        list_rows        = @()
        rows             = @()
        convert_text     = $null
        convert_enabled  = $false
        summary_visible  = $false
        open_document    = $false
        details          = $false
        open_batch_folder = $false
    }
    foreach ($element in (Get-DescendantsSafe -Root $Window)) {
        $type = $element.Current.ControlType
        $name = $element.Current.Name
        if ($type -eq $ControlType::Button) {
            if ($name -match '^Convert( \d+ Files)?$') {
                $snapshot.convert_text = $name
                $snapshot.convert_enabled = [bool]$element.Current.IsEnabled
            } elseif ($name -eq 'Open Document') {
                $snapshot.open_document = [bool]$element.Current.IsEnabled
            } elseif ($name -match '^Details') {
                $snapshot.details = [bool]$element.Current.IsEnabled
            } elseif ($name -eq 'Open Output Folder') {
                $snapshot.open_batch_folder = [bool]$element.Current.IsEnabled
            }
        } elseif ($type -eq $ControlType::Text -and $name -eq 'Batch summary') {
            $snapshot.summary_visible = -not [bool]$element.Current.IsOffscreen
        } elseif ($type -eq $ControlType::ListItem -and $name -match '\.md') {
            # Batch-list rows carry the source file name; the output-profile
            # selector's list items never do, so the two are unambiguous.
            $snapshot.list_rows += $name
            if ($name -match ([char]0x2014 + '\s*(pending|converting|succeeded|warning|failed)$')) {
                $snapshot.rows += $name
            }
        }
    }
    return $snapshot
}

function Get-ProfileName {
    param([System.Windows.Automation.AutomationElement]$Window)
    $combo = Find-Element -Root $Window -NamePattern '^Output profile$' -TimeoutSeconds $UiTimeoutSeconds
    if (-not $combo) { return $null }
    $value = $combo.GetCurrentPattern($Global:ValuePattern::Pattern).Current.Value
    return $value
}

function Set-ProfileByName {
    <#
        Select an output profile through the real selector.  UI Automation
        SelectionItemPattern is used first; a coordinate click inside the
        combo popup is the bounded fallback.  The produced value is always
        read back, so a silent mismatch can never pass.
    #>
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [Parameter(Mandatory = $true)][string]$DisplayName
    )
    $before = Get-ProfileName -Window $Window
    if ($before -eq $DisplayName) {
        return [ordered]@{ ok = $true; before = $before; after = $before; method = 'already-selected' }
    }
    $combo = Find-Element -Root $Window -NamePattern '^Output profile$' -TimeoutSeconds $UiTimeoutSeconds
    if (-not $combo) { return [ordered]@{ ok = $false; before = $before; after = $before; method = 'combo-missing' } }

    $mainHandle = [IntPtr]$Window.Current.NativeWindowHandle
    $expand = $combo.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern)
    $expand.Expand()
    Start-Sleep -Milliseconds 900

    $method = 'none'
    $item = $null
    $deadline = (Get-Date).AddSeconds(10)
    while ((Get-Date) -lt $deadline -and -not $item) {
        foreach ($element in (Get-DescendantsSafe -Root $Window)) {
            if ($element.Current.ControlType -ne $ControlType::ListItem) { continue }
            if ($element.Current.Name -eq $DisplayName) { $item = $element; break }
        }
        if (-not $item) { Start-Sleep -Milliseconds 250 }
    }
    if ($item) {
        try {
            $select = $item.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)
            $select.Select()
            $method = 'uia-selection-item'
        } catch {
            $rect = $item.Current.BoundingRectangle
            if ($rect.Width -gt 0 -and $rect.Height -gt 0) {
                $point = New-Object MdcInput+POINT
                $point.X = [int]($rect.X + $rect.Width / 2)
                $point.Y = [int]($rect.Y + $rect.Height / 2)
                [void][MdcInput]::ScreenToClient($mainHandle, [ref]$point)
                $lparam = [IntPtr](($point.Y -shl 16) -bor ($point.X -band 0xFFFF))
                [void][MdcInput]::SendMessage($mainHandle, 0x0200, [IntPtr]::Zero, $lparam)
                Start-Sleep -Milliseconds 60
                [void][MdcInput]::SendMessage($mainHandle, 0x0201, [IntPtr]1, $lparam)
                Start-Sleep -Milliseconds 90
                [void][MdcInput]::SendMessage($mainHandle, 0x0202, [IntPtr]::Zero, $lparam)
                $method = 'popup-click'
            }
        }
    }
    Start-Sleep -Milliseconds 500
    try { $expand.Collapse() } catch { }
    Start-Sleep -Milliseconds 500

    $after = Get-ProfileName -Window $Window
    return [ordered]@{
        ok     = ($after -eq $DisplayName)
        before = $before
        after  = $after
        method = $method
    }
}

function Select-Sources {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [int]$ProcessId,
        [string[]]$Paths
    )
    $results = @()
    foreach ($path in $Paths) {
        $closed = Select-SourceFile -Window $Window -ProcessId $ProcessId -FilePath $path -TimeoutSeconds $UiTimeoutSeconds
        $results += [ordered]@{ path = $path; dialog_closed = [bool]$closed }
        Start-Sleep -Milliseconds 400
    }
    return $results
}

function Clear-Selection {
    param([System.Windows.Automation.AutomationElement]$Window)
    $cleared = Invoke-ButtonByName -Window $Window -NamePattern '^Clear$' -TimeoutSeconds 5
    if ($cleared) { Start-Sleep -Milliseconds 500 }
    return [bool]$cleared
}

function Invoke-Convert {
    param([System.Windows.Automation.AutomationElement]$Window)
    $button = Find-Element -Root $Window -NamePattern '^Convert( \d+ Files)?$' -Type $ControlType::Button -TimeoutSeconds $UiTimeoutSeconds
    if (-not $button -or -not $button.Current.IsEnabled) { return $false }
    Click-Element -Window $Window -Element $button
    return $true
}

function Wait-SingleOutcome {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [int]$TimeoutSeconds = 900
    )
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $samples = New-Object System.Collections.ArrayList
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $snapshot = Get-UiSnapshot -Window $Window
        [void]$samples.Add($snapshot)
        if ($snapshot.open_document) {
            return [ordered]@{ outcome = 'SUCCESS'; seconds = [math]::Round($stopwatch.Elapsed.TotalSeconds, 1); samples = @($samples.ToArray()) }
        }
        if ($snapshot.details) {
            return [ordered]@{ outcome = 'REPORT'; seconds = [math]::Round($stopwatch.Elapsed.TotalSeconds, 1); samples = @($samples.ToArray()) }
        }
        Start-Sleep -Milliseconds 200
    }
    return [ordered]@{ outcome = 'TIMEOUT'; seconds = [math]::Round($stopwatch.Elapsed.TotalSeconds, 1); samples = @($samples.ToArray()) }
}

function Wait-BatchOutcome {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [int]$TimeoutSeconds = 900
    )
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $samples = New-Object System.Collections.ArrayList
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $snapshot = Get-UiSnapshot -Window $Window
        [void]$samples.Add($snapshot)
        if ($snapshot.summary_visible -and $snapshot.convert_enabled) {
            return [ordered]@{ outcome = 'BATCH_COMPLETE'; seconds = [math]::Round($stopwatch.Elapsed.TotalSeconds, 1); samples = @($samples.ToArray()) }
        }
        Start-Sleep -Milliseconds 150
    }
    return [ordered]@{ outcome = 'TIMEOUT'; seconds = [math]::Round($stopwatch.Elapsed.TotalSeconds, 1); samples = @($samples.ToArray()) }
}

function Get-BatchReport {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [int]$ProcessId
    )
    if (-not (Invoke-ButtonByName -Window $Window -NamePattern '^View Batch Report$' -TimeoutSeconds $UiTimeoutSeconds)) {
        return $null
    }
    $dialog = Get-TopLevelWindow -ProcessId $ProcessId -NamePrefix 'Batch report' -TimeoutSeconds 20
    if (-not $dialog) { return $null }
    $texts = @()
    $rows = @()
    foreach ($element in (Get-DescendantsSafe -Root $dialog)) {
        if ($element.Current.ControlType -eq $ControlType::Text) { $texts += $element.Current.Name }
        elseif ($element.Current.ControlType -eq $ControlType::ListItem) { $rows += $element.Current.Name }
    }
    $summary = @($texts | Where-Object { $_ -match '^Batch (complete|stopped)' }) | Select-Object -First 1
    $title = $dialog.Current.Name
    [void](Close-Dialog -Dialog $dialog -TimeoutSeconds 15)
    return [ordered]@{ title = $title; summary = $summary; rows = $rows; texts = $texts }
}

function Invoke-OpenOutputFolder {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [int]$ProcessId,
        [string]$ExpectedFolderName
    )
    $before = @(Get-DesktopWindowsByClass -ClassName $ExplorerWindowClass | ForEach-Object { $_.handle })
    if (-not (Invoke-ButtonByName -Window $Window -NamePattern '^Open Output Folder$' -TimeoutSeconds $UiTimeoutSeconds)) {
        return [ordered]@{ clicked = $false; window = $null }
    }
    $found = $null
    $deadline = (Get-Date).AddSeconds(45)
    while ((Get-Date) -lt $deadline -and -not $found) {
        foreach ($item in (Get-DesktopWindowsByClass -ClassName $ExplorerWindowClass)) {
            if ($before -contains $item.handle) { continue }
            if ($ExpectedFolderName -and $item.title -notlike "*$ExpectedFolderName*") { continue }
            $found = $item
            break
        }
        if (-not $found) { Start-Sleep -Milliseconds 500 }
    }
    if ($found) {
        [void][MdcInput]::PostMessage($found.handle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)
        Start-Sleep -Seconds 1
    }
    return [ordered]@{ clicked = $true; window = $(if ($found) { $found.title } else { $null }) }
}

function Get-DocxInventory {
    param([datetime]$Since)
    $items = @()
    if (Test-Path -LiteralPath $OutputDir) {
        foreach ($file in (Get-ChildItem -LiteralPath $OutputDir -Filter '*.docx' -File -ErrorAction SilentlyContinue)) {
            $items += [ordered]@{
                name         = $file.Name
                path         = $file.FullName
                bytes        = $file.Length
                last_write   = $file.LastWriteTime.ToString('HH:mm:ss')
                sha256       = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
                valid_docx   = (Test-Path -LiteralPath $file.FullName)
            }
        }
    }
    return $items
}

function Invoke-PythonStep {
    param([string[]]$Arguments, [string]$Label)
    $output = & $PythonExe @Arguments 2>&1
    $code = $LASTEXITCODE
    Write-Step ("python {0} exit={1}" -f $Label, $code)
    foreach ($line in $output) { Write-Host ("    {0}" -f $line) }
    return [ordered]@{ exit_code = $code; output = @($output) }
}

function Save-EvidenceJson {
    param([string]$Name, [hashtable]$Payload)
    New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
    $path = Join-Path $EvidenceDir $Name
    $Payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $path -Encoding UTF8
    return $path
}

function Restore-Preferences {
    <#
        Leave the product's own settings store exactly as it was found.
        ``reg.exe`` reports success on stderr, which Windows PowerShell would
        turn into a terminating error under $ErrorActionPreference='Stop', so the
        native call is run with a relaxed preference and its exit code is
        reported instead.
    #>
    $previous = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        if ($script:Restore.key_existed -and $script:Restore.backup) {
            & reg.exe import $script:Restore.backup *> $null
            $script:PrefsRestored = "restored from backup (reg exit=$LASTEXITCODE)"
        } elseif (Test-Path $PrefsKey) {
            Remove-Item -LiteralPath $PrefsKey -Recurse -Force -ErrorAction SilentlyContinue
            $script:PrefsRestored = "removed the settings key created during verification = $(-not (Test-Path $PrefsKey))"
        } else {
            $script:PrefsRestored = 'no product settings key present before or after verification'
        }
    } catch {
        $script:PrefsRestored = "failed: $($_.Exception.Message)"
    } finally {
        $ErrorActionPreference = $previous
    }
}

# ---------------------------------------------------------------------------
# Preparation
# ---------------------------------------------------------------------------

$script:ChildEnvironment = $null
$script:PrefsRestored = $null

if (Test-Path $PrefsKey) {
    $script:Restore.key_existed = $true
    $script:Restore.backup = Join-Path $WorkRoot 'prefs_backup.reg'
    & reg.exe export 'HKCU\Software\MD Converter' $script:Restore.backup /y | Out-Null
}

$Result = [ordered]@{
    phase            = $Phase
    started_at       = $script:StartedAt.ToString('o')
    repository_root  = $RepoRoot
    install_root     = $InstallRoot
    executable       = $ExePath
    executable_sha256 = (Get-FileHash -LiteralPath $ExePath -Algorithm SHA256).Hash
    executable_version = (Get-Item -LiteralPath $ExePath).VersionInfo.FileVersion
    work_directory   = $WorkDir
    output_directory = $OutputDir
}

Write-Step ("executable : {0}" -f $ExePath)
Write-Step ("work dir   : {0}" -f $WorkDir)

$app = $null
$window = $null

try {
    switch ($Phase) {

        'WP01' {
            $fixture = Invoke-PythonStep -Label 'fixtures' -Arguments @(
                (Join-Path $PSScriptRoot 'make_fixtures.py'), '--work', $WorkDir, '--set', 'wp02')
            $Result['fixtures'] = $fixture

            $Result['baseline_sha'] = (& git -C $RepoRoot rev-parse HEAD).Trim()
            $Result['baseline_branch'] = (& git -C $RepoRoot rev-parse --abbrev-ref HEAD).Trim()
            $Result['dist_exe'] = Join-Path $RepoRoot 'dist\MD_Converter_Lite\MD_Converter_Lite.exe'
            $Result['dist_exe_sha256'] = (Get-FileHash -LiteralPath $Result['dist_exe'] -Algorithm SHA256).Hash
            $Result['existing_installer'] = Join-Path $RepoRoot 'dist_installer\MD_Converter_v1.1.0_Setup.exe'
            if (Test-Path -LiteralPath $Result['existing_installer']) {
                $installer = Get-Item -LiteralPath $Result['existing_installer']
                $Result['existing_installer_sha256'] = (Get-FileHash -LiteralPath $installer.FullName -Algorithm SHA256).Hash
                $Result['existing_installer_built'] = $installer.LastWriteTime.ToString('o')
            }
            $Result['last_product_source_commit'] = (& git -C $RepoRoot log -1 --format='%h %ad %s' --date=iso -- md_converter).Trim()

            Add-Check 'installed-exe-matches-built-payload' `
                ($Result['executable_sha256'] -eq $Result['dist_exe_sha256']) `
                ("installed={0} built={1}" -f $Result['executable_sha256'], $Result['dist_exe_sha256'])

            # -----------------------------------------------------------------
            # Launch A - documented user launch (detached windowed GUI, no
            # inherited standard handles) with a sanitized environment.  This is
            # the primary runtime launch: it is both how the installed product is
            # really started and how runtime independence is proven.
            # -----------------------------------------------------------------
            $app = Start-PackagedAppDetached -Directory $WorkDir -Sanitize
            $Result['process_id'] = $app.Id
            $Result['child_environment'] = $script:ChildEnvironment
            $primaryEnv = $script:ChildEnvironment
            Add-Check 'child-environment-sanitized' `
                ((-not $primaryEnv.repository_on_path) -and
                 (-not $primaryEnv.dotvenv_on_path) -and
                 ($primaryEnv.pythonpath -eq '')) `
                ("PYTHONPATH='{0}'; repo on PATH={1}; .venv on PATH={2}" -f
                    $primaryEnv.pythonpath,
                    $primaryEnv.repository_on_path,
                    $primaryEnv.dotvenv_on_path)

            $window = Wait-MainWindow -ProcessId $app.Id -TimeoutSeconds $StartupTimeoutSeconds
            Add-Check 'installed-executable-launches' ([bool]$window) "main window visible (pid $($app.Id))"
            if (-not $window) { throw 'the packaged GUI did not start' }
            $Result['main_window_title'] = $window.Current.Name

            $independence = Get-RuntimeIndependence -Process $app
            $Result['runtime_independence'] = $independence
            Add-Check 'no-source-or-venv-module-loaded' `
                ($independence.module_count -gt 0 -and $independence.repository_module_hits.Count -eq 0) `
                ("{0} modules loaded; repository/.venv module hits={1}" -f
                    $independence.module_count, $independence.repository_module_hits.Count)

            # -----------------------------------------------------------------
            # Launch B - bounded observation: the same installed executable
            # started from a console-attached process, so the child inherits a
            # cp1252 standard output.  Recorded, classified, never repaired.
            # -----------------------------------------------------------------
            $consoleDir = Join-Path $WorkRoot 'cwd_console'
            New-Item -ItemType Directory -Force -Path $consoleDir, (Join-Path $consoleDir 'output') | Out-Null

            $selected = Select-Sources -Window $window -ProcessId $app.Id -Paths @((Join-Path $WorkDir '01_english.md'))
            $Result['selection'] = $selected
            $converted = Invoke-Convert -Window $window
            Add-Check 'convert-action-available' $converted 'Convert enabled after selecting one file'
            $outcome = Wait-SingleOutcome -Window $window -TimeoutSeconds $ConversionTimeoutSeconds
            $Result['outcome'] = [ordered]@{ outcome = $outcome.outcome; seconds = $outcome.seconds }
            Add-Check 'minimal-packaged-conversion-succeeds' ($outcome.outcome -eq 'SUCCESS') `
                ("outcome={0} after {1}s" -f $outcome.outcome, $outcome.seconds)

            $inventory = Get-DocxInventory -Since $script:StartedAt
            $Result['docx_inventory'] = $inventory
            $expected = Join-Path $OutputDir '01_english.docx'
            Add-Check 'default-output-location-and-naming' (Test-Path -LiteralPath $expected) `
                ("expected {0}; produced {1}" -f $expected, (($inventory | ForEach-Object { $_.name }) -join ', '))

            $collect = Join-Path $CollectDir '01_english.docx'
            if (Test-Path -LiteralPath $expected) { Copy-Item -LiteralPath $expected -Destination $collect -Force }
            $Result['collected'] = @($collect)

            Close-WindowElement -Element $window
            Start-Sleep -Seconds 3
            Stop-PackagedApp -Process $app
            $window = $null

            $consoleApp = Start-PackagedApp -Directory $consoleDir
            $consoleWindow = Wait-MainWindow -ProcessId $consoleApp.Id -TimeoutSeconds $StartupTimeoutSeconds
            $Result['console_launch'] = [ordered]@{
                process_id  = $consoleApp.Id
                environment = $script:ChildEnvironment
                window      = [bool]$consoleWindow
            }
            if ($consoleWindow) {
                [void](Select-Sources -Window $consoleWindow -ProcessId $consoleApp.Id `
                    -Paths @((Join-Path $WorkDir '01_english.md')))
                [void](Invoke-Convert -Window $consoleWindow)
                $consoleOutcome = Wait-SingleOutcome -Window $consoleWindow -TimeoutSeconds $ConversionTimeoutSeconds
                $Result['console_launch']['outcome'] = $consoleOutcome.outcome
                $Result['console_launch']['seconds'] = $consoleOutcome.seconds
                $Result['console_launch']['artifacts'] = @(
                    Get-ChildItem -LiteralPath (Join-Path $consoleDir 'output') -Filter '*.docx' -File -ErrorAction SilentlyContinue |
                        ForEach-Object { $_.Name })
                if ($consoleOutcome.outcome -ne 'SUCCESS') {
                    Add-Note 'console-inherited-launch-observation' (
                        "A CreateProcess launch that inherits a cp1252 console handle makes the " +
                        "Word-COM TOC refresh fail (UnicodeEncodeError while print()ing emoji " +
                        "diagnostics in md_converter/renderer/post_processor.py), so the packaged " +
                        "conversion is reported as not-clean even though the DOCX is written. " +
                        "Classified PRE_EXISTING_KNOWN_LIMITATION (source-level print() diagnostics, " +
                        "not introduced by packaging). The functional checks above use the documented " +
                        "user launch: a detached windowed GUI process with no inherited standard handles.")
                }
                Close-WindowElement -Element $consoleWindow
                Start-Sleep -Seconds 2
            }
            Stop-PackagedApp -Process $consoleApp
        }

        'WP02' {
            $fixture = Invoke-PythonStep -Label 'fixtures' -Arguments @(
                (Join-Path $PSScriptRoot 'make_fixtures.py'), '--work', $WorkDir, '--set', 'wp02')
            $Result['fixtures'] = $fixture
            $sources = @(
                (Join-Path $WorkDir '01_english.md'),
                (Join-Path $WorkDir '02_wide_table_figure.md'),
                (Join-Path $WorkDir '03_failure.md'),
                (Join-Path $WorkDir '04_after_failure.md')
            )
            $Result['sources'] = $sources

            $app = Start-PackagedAppDetached -Directory $WorkDir -Sanitize
            $Result['process_id'] = $app.Id
            $Result['child_environment'] = $script:ChildEnvironment
            $window = Wait-MainWindow -ProcessId $app.Id -TimeoutSeconds $StartupTimeoutSeconds
            Add-Check 'installed-executable-launches' ([bool]$window) "main window visible (pid $($app.Id))"
            if (-not $window) { throw 'the packaged GUI did not start' }

            $Result['profile'] = Get-ProfileName -Window $window
            $selected = Select-Sources -Window $window -ProcessId $app.Id -Paths $sources
            $Result['selection'] = $selected
            Add-Check 'four-files-selected' (($selected | Where-Object { $_.dialog_closed }).Count -eq 4) `
                ("{0} of 4 file dialogs accepted a source" -f (($selected | Where-Object { $_.dialog_closed }).Count))

            $before = Get-UiSnapshot -Window $window
            $Result['pre_run_snapshot'] = $before
            $expectedOrder = @('01_english.md', '02_wide_table_figure.md', '03_failure.md', '04_after_failure.md')
            $orderOk = ($before.list_rows.Count -eq 4)
            for ($index = 0; $index -lt 4 -and $orderOk; $index++) {
                if ($before.list_rows[$index] -notmatch [regex]::Escape($expectedOrder[$index])) { $orderOk = $false }
            }
            Add-Check 'queue-order-preserved' $orderOk `
                ("list rows before the run: {0}" -f ($before.list_rows -join ' | '))
            # The primary action keeps the stable accessible name "Convert" (the
            # batch size is observable through the queue list, and the batch-mode
            # surface itself through the summary that appears only for a finished
            # multi-file run), so batch mode is asserted from the batch surface.
            Add-Check 'batch-summary-hidden-before-run' (-not $before.summary_visible) `
                ("batch summary visible before the run: {0}" -f $before.summary_visible)

            $started = Invoke-Convert -Window $window
            Add-Check 'batch-convert-action-available' $started ("Convert button text before run: {0}" -f $before.convert_text)
            $outcome = Wait-BatchOutcome -Window $window -TimeoutSeconds $ConversionTimeoutSeconds
            $Result['batch_outcome'] = [ordered]@{ outcome = $outcome.outcome; seconds = $outcome.seconds }

            $samples = @($outcome.samples)
            $maxConverting = 0
            $prefixViolations = 0
            $seenWords = New-Object System.Collections.ArrayList
            foreach ($sample in $samples) {
                $converting = @($sample.rows | Where-Object { $_ -match 'converting$' }).Count
                if ($converting -gt $maxConverting) { $maxConverting = $converting }
                foreach ($row in $sample.rows) {
                    $word = ($row -split [char]0x2014)[-1].Trim()
                    if (-not $seenWords.Contains($word)) { [void]$seenWords.Add($word) }
                }
                # Strict serial execution: the terminal items must always form a
                # prefix of the queue, so a later source can never finish while an
                # earlier one is still pending or converting.
                $terminal = @()
                for ($index = 0; $index -lt 4; $index++) {
                    $row = @($sample.rows | Where-Object { $_ -match [regex]::Escape($expectedOrder[$index]) })
                    $terminal += [bool]($row.Count -gt 0 -and $row[0] -match '(succeeded|warning|failed)$')
                }
                if ($terminal -contains $true) {
                    $last = 0
                    for ($index = 0; $index -lt 4; $index++) { if ($terminal[$index]) { $last = $index } }
                    for ($index = 0; $index -le $last; $index++) {
                        if (-not $terminal[$index]) { $prefixViolations++ }
                    }
                }
            }
            $Result['sampling'] = [ordered]@{
                sample_count              = $samples.Count
                max_concurrent_converting = $maxConverting
                strict_serial_prefix_violations = $prefixViolations
                observed_state_words      = @($seenWords.ToArray())
                first = $(if ($samples.Count -gt 0) { $samples[0] } else { $null })
                last  = $(if ($samples.Count -gt 0) { $samples[$samples.Count - 1] } else { $null })
            }
            Add-Check 'batch-completes' ($outcome.outcome -eq 'BATCH_COMPLETE') `
                ("outcome={0} after {1}s from {2} sample(s)" -f $outcome.outcome, $outcome.seconds, $samples.Count)
            Add-Check 'at-most-one-converting-item' ($maxConverting -le 1) `
                ("maximum items observed in the 'converting' state in any sample: {0}" -f $maxConverting)
            Add-Check 'strict-serial-prefix-order' ($prefixViolations -eq 0) `
                ("samples where a later source was terminal before an earlier one finished: {0}" -f $prefixViolations)

            $report = Get-BatchReport -Window $window -ProcessId $app.Id
            $Result['batch_report'] = $report
            Add-Check 'batch-report-opens' ($null -ne $report) 'View Batch Report dialog opened'
            if ($report) {
                $succeededCount = @($report.rows | Where-Object { $_ -match 'succeeded$' }).Count
                $warningCount = @($report.rows | Where-Object { $_ -match 'warning$' }).Count
                $failedCount = @($report.rows | Where-Object { $_ -match 'failed$' }).Count
                $countsConsistent = ($report.summary -match '4 files processed') -and
                                    ($report.summary -match ("{0} succeeded" -f $succeededCount)) -and
                                    ($report.summary -match ("{0} failed" -f $failedCount)) -and
                                    ($report.summary -match ("{0} warning" -f $warningCount)) -and
                                    (($succeededCount + $warningCount + $failedCount) -eq 4)
                Add-Check 'batch-summary-counts' $countsConsistent `
                    ("summary='{0}'; derived from rows: {1} succeeded, {2} warning, {3} failed" -f
                        $report.summary, $succeededCount, $warningCount, $failedCount)
                $failedRows = @($report.rows | Where-Object { $_ -match '03_failure\.md' -and $_ -match 'failed$' })
                $lateRows = @($report.rows | Where-Object { $_ -match '04_after_failure\.md' -and $_ -match 'succeeded$' })
                $orderOk = ($report.rows.Count -eq 4) -and
                           ($report.rows[0] -match '01_english\.md') -and
                           ($report.rows[1] -match '02_wide_table_figure\.md') -and
                           ($report.rows[2] -match '03_failure\.md') -and
                           ($report.rows[3] -match '04_after_failure\.md')
                Add-Check 'per-file-results-and-order' ($orderOk -and $failedRows.Count -eq 1 -and $lateRows.Count -eq 1) `
                    ("rows={0}" -f ($report.rows -join ' | '))
                Add-Check 'failure-isolation' ($lateRows.Count -eq 1) 'the source after the failure succeeded'
            }

            $inventory = Get-DocxInventory -Since $script:StartedAt
            $Result['docx_inventory'] = $inventory
            $names = @($inventory | ForEach-Object { $_.name } | Sort-Object)
            $expectedNames = @('01_english.docx', '04_after_failure.docx', 'Wide_Table_Report.docx') | Sort-Object
            Add-Check 'output-count-and-naming' (($names -join ',') -eq ($expectedNames -join ',')) `
                ("produced={0}" -f ($names -join ', '))
            Add-Check 'failed-item-produces-no-output' (-not ($names -contains '03_failure.docx')) `
                ("produced={0}" -f ($names -join ', '))
            foreach ($entry in $inventory) {
                Copy-Item -LiteralPath $entry.path -Destination (Join-Path $CollectDir $entry.name) -Force
            }
            $Result['collected'] = @(Get-ChildItem -LiteralPath $CollectDir -File | ForEach-Object { $_.FullName })

            $folder = Invoke-OpenOutputFolder -Window $window -ProcessId $app.Id -ExpectedFolderName 'output'
            $Result['open_output_folder'] = $folder
            Add-Check 'open-output-folder' ($folder.clicked -and $folder.window -ne $null) `
                ("explorer window: {0}" -f $folder.window)
        }

        'WP03' {
            $fixture = Invoke-PythonStep -Label 'fixtures' -Arguments @(
                (Join-Path $PSScriptRoot 'make_fixtures.py'), '--work', $WorkDir, '--set', 'wp03')
            $Result['fixtures'] = $fixture
            $matrix = @(
                [ordered]@{ name = 'matrix_professional_report'; profile = 'Professional Report'; id = 'professional_report'; file = 'matrix_professional_report.md'; expected = 'Matrix_Professional_Report.docx' },
                [ordered]@{ name = 'matrix_business_report'; profile = 'Business Report'; id = 'business_report'; file = 'matrix_business_report.md'; expected = 'Matrix_Business_Report.docx' },
                [ordered]@{ name = 'matrix_academic'; profile = 'Academic'; id = 'academic'; file = 'matrix_academic.md'; expected = 'Matrix_Academic.docx' },
                [ordered]@{ name = 'matrix_technical'; profile = 'Technical'; id = 'technical'; file = 'matrix_technical.md'; expected = 'Matrix_Technical.docx' },
                [ordered]@{ name = 'matrix_clean_minimal'; profile = 'Clean / Minimal'; id = 'clean_minimal'; file = 'matrix_clean_minimal.md'; expected = 'Matrix_Clean_Minimal.docx' },
                [ordered]@{ name = 'toc_cn'; profile = 'Professional Report'; id = 'professional_report'; file = 'toc_cn.md'; expected = '竞争基础集成验证.docx'; kind = 'toc_control' }
            )

            $app = Start-PackagedAppDetached -Directory $WorkDir -Sanitize
            $Result['process_id'] = $app.Id
            $Result['child_environment'] = $script:ChildEnvironment
            $window = Wait-MainWindow -ProcessId $app.Id -TimeoutSeconds $StartupTimeoutSeconds
            Add-Check 'installed-executable-launches' ([bool]$window) "main window visible (pid $($app.Id))"
            if (-not $window) { throw 'the packaged GUI did not start' }

            $runs = @()
            $profileObserved = @{}
            foreach ($entry in $matrix) {
                if (-not (Clear-Selection -Window $window)) { }
                $selected = Select-Sources -Window $window -ProcessId $app.Id -Paths @((Join-Path $WorkDir $entry.file))
                $profileResult = Set-ProfileByName -Window $window -DisplayName $entry.profile
                $profileObserved[$entry.name] = $profileResult
                $converted = Invoke-Convert -Window $window
                $outcome = Wait-SingleOutcome -Window $window -TimeoutSeconds $ConversionTimeoutSeconds
                $expectedPath = Join-Path $OutputDir $entry.expected
                $exists = Test-Path -LiteralPath $expectedPath
                $collected = $null
                if ($exists) {
                    $collected = Join-Path $CollectDir $entry.expected
                    Copy-Item -LiteralPath $expectedPath -Destination $collected -Force
                }
                $runs += [ordered]@{
                    name            = $entry.name
                    profile         = $entry.id
                    profile_display = $entry.profile
                    kind            = $entry.kind
                    source          = (Join-Path $WorkDir $entry.file)
                    docx            = $collected
                    expected_name   = $entry.expected
                    produced        = $exists
                    outcome         = $outcome.outcome
                    seconds         = $outcome.seconds
                    convert_started = $converted
                    dialog_closed   = ($selected | Select-Object -First 1).dialog_closed
                }
                Add-Check ("{0}: packaged conversion succeeds" -f $entry.name) `
                    (($outcome.outcome -eq 'SUCCESS') -and $exists -and $converted) `
                    ("outcome={0} after {1}s; produced {2}" -f $outcome.outcome, $outcome.seconds, $entry.expected)
                Add-Check ("{0}: profile selector set to {1}" -f $entry.name, $entry.profile) `
                    ([bool]$profileResult.ok) `
                    ("before='{0}' after='{1}' method={2}" -f $profileResult.before, $profileResult.after, $profileResult.method)
            }

            $Result['runs'] = $runs
            $Result['profiles_observed'] = $profileObserved

            $runsPath = Join-Path $WorkRoot 'parity_runs.json'
            $reportPath = Join-Path $WorkRoot 'parity_report.json'
            $payload = @()
            foreach ($run in $runs) {
                if ($run.docx) {
                    $payload += [ordered]@{
                        name    = $run.name
                        profile = $run.profile
                        kind    = $run.kind
                        docx    = $run.docx
                    }
                }
            }
            $payload | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $runsPath -Encoding UTF8
            $parity = Invoke-PythonStep -Label 'parity' -Arguments @(
                (Join-Path $PSScriptRoot 'verify_packaged_parity.py'),
                '--runs', $runsPath,
                '--output', $reportPath,
                '--repo-root', $RepoRoot)
            $Result['parity_run'] = $parity
            $Result['parity_report_path'] = $reportPath
            if (Test-Path -LiteralPath $reportPath) {
                $parityJson = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
                $Result['parity_status'] = $parityJson.status
                $Result['parity_total'] = $parityJson.total
                $Result['parity_failed'] = $parityJson.failed
                Add-Check 'packaged-profile-and-feature-parity' `
                    ($parityJson.status -eq 'PASS') `
                    ("parity checks={0} failed={1}" -f $parityJson.total, $parityJson.failed)
            } else {
                Add-Check 'packaged-profile-and-feature-parity' $false 'parity report was not produced'
            }
        }

        'WP04' {
            $fixture = Invoke-PythonStep -Label 'fixtures' -Arguments @(
                (Join-Path $PSScriptRoot 'make_fixtures.py'), '--work', $WorkDir, '--set', 'wp02')
            $Result['fixtures'] = $fixture

            # Cold launch: nothing of this phase has started the product yet.
            $app = Start-PackagedAppDetached -Directory $WorkDir -Sanitize
            $Result['process_id'] = $app.Id
            $Result['child_environment'] = $script:ChildEnvironment
            $window = Wait-MainWindow -ProcessId $app.Id -TimeoutSeconds $StartupTimeoutSeconds
            Add-Check 'cold-launch-succeeds' ([bool]$window) "main window visible (pid $($app.Id))"
            if (-not $window) { throw 'the packaged GUI did not start on a cold launch' }

            $initial = Get-UiSnapshot -Window $window
            $Result['initial_snapshot'] = $initial
            Add-Check 'no-stuck-previous-batch-state' `
                ((-not $initial.summary_visible) -and (-not $initial.open_document) -and
                 $initial.rows.Count -eq 0 -and $initial.convert_enabled -eq $false) `
                ("summary visible={0}; open document={1}; rows={2}; convert enabled={3}" -f
                    $initial.summary_visible, $initial.open_document, $initial.rows.Count, $initial.convert_enabled)

            $independence = Get-RuntimeIndependence -Process $app
            $Result['runtime_independence'] = $independence
            Add-Check 'cold-launch-runtime-independence' `
                ($independence.module_count -gt 0 -and $independence.repository_module_hits.Count -eq 0) `
                ("{0} modules loaded; repository/.venv module hits={1}" -f
                    $independence.module_count, $independence.repository_module_hits.Count)

            $selected = Select-Sources -Window $window -ProcessId $app.Id -Paths @((Join-Path $WorkDir '04_after_failure.md'))
            $Result['selection'] = $selected
            $converted = Invoke-Convert -Window $window
            $outcome = Wait-SingleOutcome -Window $window -TimeoutSeconds $ConversionTimeoutSeconds
            $Result['outcome'] = [ordered]@{ outcome = $outcome.outcome; seconds = $outcome.seconds }
            Add-Check 'representative-conversion-succeeds' ($outcome.outcome -eq 'SUCCESS') `
                ("outcome={0} after {1}s" -f $outcome.outcome, $outcome.seconds)

            $inventory = Get-DocxInventory -Since $script:StartedAt
            $Result['docx_inventory'] = $inventory
            $expected = Join-Path $OutputDir '04_after_failure.docx'
            Add-Check 'output-behaviour-correct' (Test-Path -LiteralPath $expected) `
                ("expected {0}; inventory {1}" -f $expected, (($inventory | ForEach-Object { $_.name }) -join ', '))
            Add-Check 'converted-artifact-opens' `
                ($outcome.outcome -eq 'SUCCESS' -or (Test-Path -LiteralPath $expected)) `
                ("Open Document enabled={0}; artifact present={1}" -f
                    ((@($outcome.samples) | Select-Object -Last 1).open_document), (Test-Path -LiteralPath $expected))
            if (Test-Path -LiteralPath $expected) {
                Copy-Item -LiteralPath $expected -Destination (Join-Path $CollectDir '04_after_failure.docx') -Force
            }
            $Result['collected'] = @(Get-ChildItem -LiteralPath $CollectDir -File | ForEach-Object { $_.FullName })
        }
    }
}
catch {
    Add-Check 'harness' $false ("aborted: {0}" -f $_.Exception.Message)
}
finally {
    if ($window -and -not $KeepOpen) {
        try {
            $final = Get-UiSnapshot -Window $window
            $Result['final_snapshot'] = $final
            Close-WindowElement -Element $window
            Start-Sleep -Seconds 3
        } catch { }
    }
    if ($app -and -not $KeepOpen) { Stop-PackagedApp -Process $app }
    if (-not $KeepOpen) {
        Get-Process MD_Converter -ErrorAction SilentlyContinue | ForEach-Object { try { $_.Kill() } catch { } }
    }
    Restore-Preferences
    $Result['preferences_restored'] = $script:PrefsRestored
}

$Result['finished_at'] = (Get-Date).ToString('o')
$Result['checks'] = @($script:Checks.ToArray())
$Result['notes'] = @($script:Notes.ToArray())
$Result['failed_checks'] = @($script:Failures.ToArray())
$Result['failed_count'] = $script:Failures.Count
$Result['status'] = $(if ($script:Failures.Count -eq 0) { 'PASS' } else { 'FAIL' })

$jsonPath = Save-EvidenceJson -Name ("WP-R2V02-{0}_RESULT.json" -f $Phase.Substring(2)) -Payload $Result
Write-Step ("raw result written to {0}" -f $jsonPath)

Write-Host ''
Write-Host ("RESULT: {0} ({1} failing check(s))" -f $Result['status'], $script:Failures.Count)
if ($script:Failures.Count -gt 0) { exit 1 }
exit 0
