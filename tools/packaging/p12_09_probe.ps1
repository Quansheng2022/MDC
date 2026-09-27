#requires -Version 5.1
<#
.SYNOPSIS
    Diagnostic probe: dump UIA element state for the packaged GUI.

.DESCRIPTION
    Verification helper used while building the P12-09 acceptance harness.  It
    launches the packaged executable, selects a Markdown file, optionally runs a
    conversion, and prints every descendant element (control type, name,
    enabled, off-screen) so the acceptance checks can be calibrated against the
    real accessibility tree.  It changes no product behaviour.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ExePath,
    [Parameter(Mandatory = $true)][string]$InputMarkdown,
    [switch]$Convert,
    [int]$ConversionTimeoutSeconds = 300,
    [string]$WorkDir
)

. "$PSScriptRoot\gui_automation.ps1"

if (-not $WorkDir) { $WorkDir = Join-Path $env:TEMP ("mdc_probe_" + (Get-Date -Format 'HHmmss')) }
New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
$ExePath = (Resolve-Path -LiteralPath $ExePath).Path
$InputMarkdown = (Resolve-Path -LiteralPath $InputMarkdown).Path

function Dump-Elements {
    param([System.Windows.Automation.AutomationElement]$Window, [string]$Label)
    Write-Host ("===== {0} =====" -f $Label)
    foreach ($element in Get-Descendants -Root $Window) {
        $type = $element.Current.ControlType.ProgrammaticName -replace '^ControlType\.', ''
        Write-Host ("{0} | name='{1}' | enabled={2} | offscreen={3}" -f $type, $element.Current.Name, $element.Current.IsEnabled, $element.Current.IsOffscreen)
    }
}

$app = Start-Process -FilePath $ExePath -WorkingDirectory $WorkDir -PassThru
try {
    $window = Get-TopLevelWindow -ProcessId $app.Id -Name 'MD Converter' -TimeoutSeconds 60
    if (-not $window) { throw 'window did not appear' }
    Dump-Elements -Window $window -Label 'EMPTY'

    $null = Select-SourceFile -Window $window -ProcessId $app.Id -FilePath $InputMarkdown
    Start-Sleep -Seconds 1
    Dump-Elements -Window $window -Label 'AFTER SELECT'

    if ($Convert) {
        $convertButton = Wait-ForConvertEnabled -Window $window -TimeoutSeconds 30
        if ($convertButton) {
            Click-Element -Window $window -Element $convertButton
            Start-Sleep -Seconds $ConversionTimeoutSeconds
            Dump-Elements -Window $window -Label 'AFTER CONVERT'
        }
    }
}
finally {
    try { $app.Refresh(); if (-not $app.HasExited) { $app.Kill() } } catch { }
    Get-Process MD_Converter_Lite -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}
