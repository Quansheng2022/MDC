#requires -Version 5.1
<#
.SYNOPSIS
    R2-V02 harness probe: dump the packaged GUI accessibility tree.

.DESCRIPTION
    Verification tooling only (no product behaviour is touched).  It launches
    the *installed* packaged executable from a neutral working directory with a
    sanitized child environment, then records the UI Automation tree of the
    main window (and of the expanded output-profile selector) so the WP-02/WP-03
    harnesses can be written against the real control names.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ExePath,
    [string]$WorkDir,
    [string]$EvidencePath
)

$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
. (Join-Path $RepoRoot 'tools\packaging\gui_automation.ps1')

if (-not $WorkDir) {
    $WorkDir = Join-Path $env:TEMP ("mdc_r2v02_probe_" + (Get-Date -Format 'yyyyMMdd_HHmmss'))
}
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $WorkDir 'output') | Out-Null

function Get-SanitizedPath {
    param([string]$Separator = ';')
    $repoPattern = [regex]::Escape($RepoRoot)
    $kept = @()
    foreach ($entry in ($env:PATH -split [regex]::Escape($Separator))) {
        if (-not $entry) { continue }
        if ($entry -match $repoPattern) { continue }
        if ($entry -match '\\\.venv\\') { continue }
        $kept += $entry
    }
    return ($kept -join $Separator)
}

$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = (Resolve-Path -LiteralPath $ExePath).Path
$psi.WorkingDirectory = $WorkDir
$psi.UseShellExecute = $false
$psi.Environment.Remove('PYTHONPATH') | Out-Null
$psi.Environment.Remove('PYTHONHOME') | Out-Null
$psi.Environment.Remove('PYTHONSTARTUP') | Out-Null
$psi.Environment['PATH'] = Get-SanitizedPath

$result = [ordered]@{
    executable = $psi.FileName
    work_dir = $WorkDir
    child_path = $psi.Environment['PATH']
    child_pythonpath = "$($psi.Environment['PYTHONPATH'])"
    started_at = (Get-Date).ToString('o')
}

$process = [System.Diagnostics.Process]::Start($psi)
$result['process_id'] = $process.Id

$window = $null
$deadline = (Get-Date).AddSeconds(90)
while ((Get-Date) -lt $deadline -and -not $window) {
    $window = Get-TopLevelWindow -ProcessId $process.Id -Name 'MD Converter' -TimeoutSeconds 2
}
$result['startup_ok'] = [bool]$window

if ($window) {
    $result['main_window_title'] = $window.Current.Name
    $tree = New-Object System.Collections.ArrayList
    foreach ($element in Get-Descendants -Root $window) {
        [void]$tree.Add([ordered]@{
                type = $element.Current.ControlType.ProgrammaticName
                name = $element.Current.Name
                enabled = [bool]$element.Current.IsEnabled
                offscreen = [bool]$element.Current.IsOffscreen
                aw = $element.Current.AutomationId
            })
    }
    $result['main_window_tree'] = @($tree.ToArray())

    $modulePaths = @()
    try {
        foreach ($module in $process.Modules) {
            $modulePaths += $module.FileName
        }
    } catch {
        $modulePaths += "module enumeration failed: $($_.Exception.Message)"
    }
    $result['module_paths'] = $modulePaths

    # Expand the output-profile selector and dump what UI Automation exposes.
    $combo = Find-Element -Root $window -NamePattern '^Output profile$' -TimeoutSeconds 10
    if ($combo) {
        $result['profile_combo_type'] = $combo.Current.ControlType.ProgrammaticName
        $result['profile_combo_value'] = "$($combo.GetCurrentPropertyValue([System.Windows.Automation.ValuePattern]::ValueProperty))"
        $patterns = @()
        foreach ($pattern in $combo.GetSupportedPatterns()) { $patterns += $pattern.ProgrammaticName }
        $result['profile_combo_patterns'] = $patterns
        try {
            $expand = $combo.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern)
            $expand.Expand()
            Start-Sleep -Milliseconds 1200
        } catch {
            $result['profile_combo_expand_error'] = $_.Exception.Message
        }
        $popupTree = New-Object System.Collections.ArrayList
        foreach ($handle in [MdcWindows]::AllHandles()) {
            $title = [MdcWindows]::Title($handle)
            $class = [MdcWindows]::ClassName($handle)
            [void]$popupTree.Add([ordered]@{ handle = "$handle"; class = $class; title = $title })
        }
        $result['desktop_windows_after_expand'] = @($popupTree.ToArray())

        $listItems = New-Object System.Collections.ArrayList
        foreach ($element in Get-Descendants -Root $window) {
            if ($element.Current.ControlType -ne $ControlType::ListItem) { continue }
            [void]$listItems.Add([ordered]@{
                    name = $element.Current.Name
                    offscreen = [bool]$element.Current.IsOffscreen
                    aw = $element.Current.AutomationId
                })
        }
        $result['list_items_after_expand'] = @($listItems.ToArray())

        try {
            $expand = $combo.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern)
            $expand.Collapse()
        } catch { }
    } else {
        $result['profile_combo_type'] = 'NOT FOUND'
    }

    $batchList = Find-Element -Root $window -NamePattern '^Markdown files in this batch$' -TimeoutSeconds 10
    $result['batch_list_found'] = [bool]$batchList
    if ($batchList) {
        $result['batch_list_type'] = $batchList.Current.ControlType.ProgrammaticName
    }

    Close-WindowElement -Element $window
    Start-Sleep -Seconds 2
}

try { $process.Refresh(); if (-not $process.HasExited) { $process.Kill() } } catch { }

$result['finished_at'] = (Get-Date).ToString('o')
if ($EvidencePath) {
    $dir = Split-Path -Parent $EvidencePath
    if ($dir) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $EvidencePath -Encoding UTF8
}
$result | ConvertTo-Json -Depth 4
exit 0
