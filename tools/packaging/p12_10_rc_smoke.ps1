#requires -Version 5.1
<#
.SYNOPSIS
    P12-10 minimal Release Candidate smoke test against the installed product.

.DESCRIPTION
    Performs the minimum post-freeze smoke required by WP-P12-10-05 and nothing
    more (P12-09 remains authoritative for the full matrices):

        installer identity precheck
          -> silent per-user install
          -> installed executable identity + notices
          -> launch the installed application
          -> About shows Version 1.1.0
          -> Settings save -> clean close -> restart -> restored (then restored back)
          -> one representative Markdown -> DOCX conversion through the GUI
          -> Open Document hands the DOCX to Microsoft Word (Word really opened it:
             Word window + exclusive file lock while displayed)
          -> clean close
          -> silent uninstall
          -> user documents and converted documents survive
          -> installer identity re-checked after the smoke (post-freeze drift = 0)

    Verification tooling only.  The script never imports or runs the source tree;
    it drives the *installed* application through real user actions (UI
    Automation plus window messages) and reimplements no product logic.

.EXAMPLE
    powershell -File tools/packaging/p12_10_rc_smoke.ps1 `
        -InstallerPath release/MD_Converter_v1.1.0_RC1/MD_Converter_v1.1.0_Setup.exe `
        -InputMarkdown Doc/V2/Implementation/P12-09/corpus/01_simple.md `
        -EvidencePath Doc/V2/Implementation/P12-10/evidence/wp05_rc_smoke.json
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$InstallerPath,
    [Parameter(Mandatory = $true)][string]$InputMarkdown,
    [string]$ExpectedInstallerSha256 = 'EFEC378F11B00A53791158199B4DC98AA09F44F5B1F013363FF744A92B91B9BF',
    [string]$ExpectedExecutableSha256 = 'F5AB988168DFA976ED50095A272FB3405CE2CAB395C4A77A34637318D60F7E04',
    [string]$WorkRoot,
    [string]$EvidencePath,
    [int]$StartupTimeoutSeconds = 90,
    [int]$UiTimeoutSeconds = 30,
    [int]$ConversionTimeoutSeconds = 900,
    [int]$WordTimeoutSeconds = 120
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\gui_automation.ps1"

$MainWindowTitle = 'MD Converter'
$InstallDir = Join-Path $env:LOCALAPPDATA 'Programs\MD_Converter'
$InstalledExe = Join-Path $InstallDir 'MD_Converter.exe'
$Uninstaller = Join-Path $InstallDir 'unins000.exe'
$UninstallKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\MDConverter.Quansheng2022_is1'
$PrefsKey = 'HKCU:\Software\MD Converter\MD Converter\folders'
$StartMenuDir = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'

$Results = [ordered]@{}
$Failures = New-Object System.Collections.ArrayList
$Observations = New-Object System.Collections.ArrayList
$StartedAt = Get-Date

function Write-Step { param([string]$Message) Write-Host ("[rc-smoke] {0}" -f $Message) }

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

function Get-StoredRememberValue {
    return (Get-ItemProperty -Path $PrefsKey -Name 'remember' -ErrorAction SilentlyContinue).remember
}

function Open-SettingsDialog {
    param(
        [System.Windows.Automation.AutomationElement]$Window,
        [int]$ProcessId
    )
    $button = Find-Element -Root $Window -NamePattern '^Settings$' -Type $ControlType::Button -TimeoutSeconds $UiTimeoutSeconds
    if (-not $button) { throw 'the Settings button was not found' }
    Click-Element -Window $Window -Element $button
    $dialog = Get-TopLevelWindow -ProcessId $ProcessId -NamePrefix 'Settings' -TimeoutSeconds $UiTimeoutSeconds
    if (-not $dialog) { throw 'the Settings dialog did not appear' }
    return $dialog
}

function Get-RememberToggle {
    param([System.Windows.Automation.AutomationElement]$Dialog)
    return (Find-Element -Root $Dialog -NamePattern '^Remember the last folders I used$' `
        -Type $ControlType::CheckBox -TimeoutSeconds $UiTimeoutSeconds)
}

function Get-ToggleState {
    param([System.Windows.Automation.AutomationElement]$Element)
    $pattern = $Element.GetCurrentPattern($TogglePattern::Pattern)
    return $pattern.Current.ToggleState
}

function Save-SettingsDialog {
    param([System.Windows.Automation.AutomationElement]$Dialog)
    $handle = [IntPtr]$Dialog.Current.NativeWindowHandle
    $save = Find-Element -Root $Dialog -NamePattern '^Save$' -Type $ControlType::Button -TimeoutSeconds $UiTimeoutSeconds
    if (-not $save) { throw 'the Save button was not found' }
    Click-Element -Window $Dialog -Element $save
    return (Wait-ForHandleGone -Handle $handle -TimeoutSeconds 20)
}

function Start-MdcApp {
    param([string]$Exe, [string]$WorkingDirectory)
    $process = Start-Process -FilePath $Exe -WorkingDirectory $WorkingDirectory -PassThru
    $window = Get-TopLevelWindow -ProcessId $process.Id -Name $MainWindowTitle -TimeoutSeconds $StartupTimeoutSeconds
    return [pscustomobject]@{ Process = $process; Window = $window }
}

function Stop-MdcApp {
    param($App)
    if (-not $App) { return $false }
    try {
        if ($App.Window) { Close-WindowElement -Element $App.Window }
        $deadline = (Get-Date).AddSeconds(30)
        while ((Get-Date) -lt $deadline) {
            $App.Process.Refresh()
            if ($App.Process.HasExited) { return $true }
            Start-Sleep -Milliseconds 400
        }
        $App.Process.Refresh()
        return [bool]$App.Process.HasExited
    } catch {
        return $false
    }
}

function Wait-ForExclusiveLock {
    param([string]$Path, [int]$TimeoutSeconds = 30)
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-FileExclusivelyLocked -Path $Path) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

# ---------------------------------------------------------------------------
# Preparation
# ---------------------------------------------------------------------------

$InstallerPath = (Resolve-Path -LiteralPath $InstallerPath).Path
$InputMarkdown = (Resolve-Path -LiteralPath $InputMarkdown).Path
if (-not $WorkRoot) {
    $WorkRoot = Join-Path $env:TEMP ('mdc_p1210_rc_smoke_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
}
New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null

$InputDir = Join-Path $WorkRoot 'input'
$OutputDir = Join-Path $WorkRoot 'output'
$UserDocDir = Join-Path $WorkRoot 'Documents\MD_Converter'
New-Item -ItemType Directory -Force -Path $InputDir, $OutputDir, $UserDocDir | Out-Null

$InputName = Split-Path -Leaf $InputMarkdown
$LocalInput = Join-Path $InputDir $InputName
Copy-Item -LiteralPath $InputMarkdown -Destination $LocalInput -Force
$Sentinel = Join-Path $UserDocDir 'user_note.txt'
Set-Content -LiteralPath $Sentinel -Value 'P12-10 RC smoke user document sentinel' -Encoding UTF8

$WordPath = Join-Path ${env:ProgramFiles} 'Microsoft Office\root\Office16\WINWORD.EXE'

$Results['installer'] = $InstallerPath
$Results['work_root'] = $WorkRoot
$Results['input_markdown'] = $LocalInput
$Results['started_at'] = $StartedAt.ToString('o')
$Results['word_path'] = $WordPath
$Results['word_version'] = $(if (Test-Path -LiteralPath $WordPath) { (Get-Item -LiteralPath $WordPath).VersionInfo.FileVersion } else { 'absent' })

$prefsExistedBefore = $null -ne (Get-StoredRememberValue)
$prefsValueBefore = Get-StoredRememberValue
$Results['prefs_remember_existed_before'] = $prefsExistedBefore
$Results['prefs_remember_value_before'] = "$prefsValueBefore"
$Results['install_dir_present_before'] = (Test-Path -LiteralPath $InstalledExe)

$app = $null
$appSecond = $null

try {
    # -----------------------------------------------------------------------
    # 1. Precheck — installer identity must equal the frozen WP-01 hash
    # -----------------------------------------------------------------------
    $installerItem = Get-Item -LiteralPath $InstallerPath
    $installerHash = (Get-FileHash -LiteralPath $InstallerPath -Algorithm SHA256).Hash
    $Results['installer_size'] = $installerItem.Length
    $Results['installer_sha256'] = $installerHash
    $Results['installer_file_version'] = $installerItem.VersionInfo.FileVersion
    Add-Check 'precheck-installer-hash' ($installerHash -eq $ExpectedInstallerSha256) ("{0}" -f $installerHash)
    Add-Check 'precheck-installer-size' ($installerItem.Length -eq 51109717) ("{0} bytes" -f $installerItem.Length)
    Add-Check 'precheck-installer-version' ($installerItem.VersionInfo.FileVersion -like '1.1.0*') ("{0}" -f $installerItem.VersionInfo.FileVersion)

    # -----------------------------------------------------------------------
    # 2. Silent per-user install
    # -----------------------------------------------------------------------
    $installProcess = Start-Process -FilePath $InstallerPath `
        -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART' -PassThru -Wait
    $Results['install_exit_code'] = $installProcess.ExitCode
    Add-Check 'install-exit-code' ($installProcess.ExitCode -eq 0) ("exit {0}" -f $installProcess.ExitCode)
    Add-Check 'install-directory-created' (Test-Path -LiteralPath $InstalledExe) ("{0}" -f $InstalledExe)

    $installedHash = (Get-FileHash -LiteralPath $InstalledExe -Algorithm SHA256).Hash
    $Results['installed_executable_sha256'] = $installedHash
    $Results['installed_executable_version'] = (Get-Item -LiteralPath $InstalledExe).VersionInfo.FileVersion
    Add-Check 'installed-executable-identity' ($installedHash -eq $ExpectedExecutableSha256) ("{0}" -f $installedHash)
    Add-Check 'installed-executable-version' ((Get-Item -LiteralPath $InstalledExe).VersionInfo.FileVersion -eq '1.1.0') `
        ("{0}" -f (Get-Item -LiteralPath $InstalledExe).VersionInfo.FileVersion)
    Add-Check 'installed-eula-and-notices' `
        ((Test-Path -LiteralPath (Join-Path $InstallDir 'EULA.txt')) -and (Test-Path -LiteralPath (Join-Path $InstallDir 'THIRD_PARTY_NOTICES.txt'))) `
        'EULA.txt + THIRD_PARTY_NOTICES.txt installed'

    if (Test-Path -LiteralPath $UninstallKey) {
        $uninstallEntry = Get-ItemProperty -Path $UninstallKey
        $Results['uninstall_display_name'] = $uninstallEntry.DisplayName
        $Results['uninstall_display_version'] = $uninstallEntry.DisplayVersion
        $Results['uninstall_publisher'] = $uninstallEntry.Publisher
        Add-Check 'uninstall-registry-entry' ($uninstallEntry.DisplayVersion -eq '1.1.0') `
            ("{0} {1} ({2})" -f $uninstallEntry.DisplayName, $uninstallEntry.DisplayVersion, $uninstallEntry.Publisher)
    } else {
        Add-Check 'uninstall-registry-entry' $false 'uninstall entry not created'
    }

    $service = Get-Service -Name 'MD_Converter' -ErrorAction SilentlyContinue
    $autoStart = (Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -ErrorAction SilentlyContinue).'MD Converter'
    Add-Check 'no-service-or-autostart-created' ((-not $service) -and (-not $autoStart)) `
        ("service={0}; autostart={1}" -f $(if ($service) { $service.Name } else { 'none' }), $(if ($autoStart) { $autoStart } else { 'none' }))

    # -----------------------------------------------------------------------
    # 3. Launch the installed application
    # -----------------------------------------------------------------------
    $app = Start-MdcApp -Exe $InstalledExe -WorkingDirectory $WorkRoot
    $Results['process_id'] = $app.Process.Id
    if (-not $app.Window) {
        Add-Check 'launch-installed-app' $false ("main window '{0}' did not appear" -f $MainWindowTitle)
        throw 'launch failed'
    }
    Add-Check 'launch-installed-app' $true ("window '{0}' is visible (pid {1})" -f $app.Window.Current.Name, $app.Process.Id)

    # -----------------------------------------------------------------------
    # 4. About dialog — version must be 1.1.0
    # -----------------------------------------------------------------------
    $aboutButton = Find-Element -Root $app.Window -NamePattern '^About$' -Type $ControlType::Button -TimeoutSeconds $UiTimeoutSeconds
    if (-not $aboutButton) {
        Add-Check 'about-version' $false 'About button not found'
    } else {
        Click-Element -Window $app.Window -Element $aboutButton
        $aboutDialog = Get-TopLevelWindow -ProcessId $app.Process.Id -NamePrefix 'About MD Converter' -TimeoutSeconds $UiTimeoutSeconds
        if (-not $aboutDialog) {
            Add-Check 'about-version' $false 'About dialog did not appear'
        } else {
            $aboutText = @(Get-Descendants -Root $aboutDialog | ForEach-Object { $_.Current.Name } | Where-Object { $_ })
            $Results['about_text'] = $aboutText
            $versionLine = @($aboutText | Where-Object { $_ -match '^\s*Version\s+\S+' })
            $null = Close-Dialog -Dialog $aboutDialog
            Add-Check 'about-version' (@($versionLine | Where-Object { $_ -match '1\.1\.0' }).Count -gt 0) `
                ("version text: {0}" -f ($versionLine -join '; '))
        }
    }

    # -----------------------------------------------------------------------
    # 5. Settings persistence — flip, save, restart, confirm, restore
    # -----------------------------------------------------------------------
    $settingsDialog = Open-SettingsDialog -Window $app.Window -ProcessId $app.Process.Id
    $toggle = Get-RememberToggle -Dialog $settingsDialog
    if (-not $toggle) {
        Add-Check 'settings-persistence' $false 'remember-folders toggle not found'
        $null = Close-Dialog -Dialog $settingsDialog
    } else {
        $stateBefore = Get-ToggleState -Element $toggle
        $Results['settings_state_before'] = "$stateBefore"
        Click-Element -Window $settingsDialog -Element $toggle
        Start-Sleep -Milliseconds 400
        $stateFlipped = Get-ToggleState -Element $toggle
        $Results['settings_state_flipped'] = "$stateFlipped"
        $saved = Save-SettingsDialog -Dialog $settingsDialog
        $storedAfterSave = "$(Get-StoredRememberValue)"
        $Results['settings_stored_after_save'] = $storedAfterSave
        $expectedStored = $(if ("$stateFlipped" -eq 'On') { 'true' } else { 'false' })
        Add-Check 'settings-save-persists' (($stateFlipped -ne $stateBefore) -and $saved -and ($storedAfterSave.ToLower() -eq $expectedStored)) `
            ("toggle {0} -> {1}; saved={2}; store.remember={3}" -f $stateBefore, $stateFlipped, $saved, $storedAfterSave)

        $closedFirst = Stop-MdcApp -App $app
        Add-Check 'clean-close-first-run' ([bool]$closedFirst) ("process exited: {0}" -f $closedFirst)

        $appFirst = $app
        $app = $null
        $appSecond = Start-MdcApp -Exe $InstalledExe -WorkingDirectory $WorkRoot
        if (-not $appSecond.Window) {
            Add-Check 'settings-restored-after-restart' $false 'application did not restart'
        } else {
            $settingsDialog2 = Open-SettingsDialog -Window $appSecond.Window -ProcessId $appSecond.Process.Id
            $toggle2 = Get-RememberToggle -Dialog $settingsDialog2
            $stateRestored = Get-ToggleState -Element $toggle2
            $Results['settings_state_after_restart'] = "$stateRestored"
            Add-Check 'settings-restored-after-restart' ("$stateRestored" -eq "$stateFlipped") `
                ("after restart the toggle reads {0} (saved {1})" -f $stateRestored, $stateFlipped)

            if ("$stateRestored" -ne "$stateBefore") {
                Click-Element -Window $settingsDialog2 -Element $toggle2
                Start-Sleep -Milliseconds 400
                $null = Save-SettingsDialog -Dialog $settingsDialog2
            } else {
                $null = Close-Dialog -Dialog $settingsDialog2
            }
        }
    }

    # -----------------------------------------------------------------------
    # 6. Real conversion through the installed GUI
    # -----------------------------------------------------------------------
    $active = if ($appSecond -and $appSecond.Window) { $appSecond } else { $app }
    if (-not $active -or -not $active.Window) { throw 'no running application window for the conversion' }

    $conversion = Convert-MarkdownThroughGui -Window $active.Window -ProcessId $active.Process.Id `
        -InputMarkdown $LocalInput -TimeoutSeconds $ConversionTimeoutSeconds
    $Results['conversion'] = $conversion
    Add-Check 'conversion-success' ($conversion.outcome.outcome -eq 'SUCCESS') `
        ("outcome={0} after {1}s ({2})" -f $conversion.outcome.outcome, $conversion.outcome.seconds, $conversion.outcome.detail)

    $artifactRoots = @($WorkRoot, $OutputDir, (Split-Path -Parent $LocalInput), (Join-Path $env:USERPROFILE 'Documents\MD_Converter'))
    $artifacts = @(Get-NewDocumentArtifacts -Since $StartedAt -Roots $artifactRoots | Sort-Object -Unique)
    $Results['docx_artifacts'] = @($artifacts)
    Add-Check 'docx-artifact-created' ($artifacts.Count -gt 0) ("{0} DOCX artifact(s)" -f $artifacts.Count)

    $validArtifacts = @($artifacts | Where-Object { Test-DocxArtifact -Path $_ })
    $Results['valid_docx_artifacts'] = @($validArtifacts)
    Add-Check 'docx-artifact-valid' ($validArtifacts.Count -gt 0) `
        ("{0} of {1} artifact(s) contain word/document.xml" -f $validArtifacts.Count, $artifacts.Count)

    # -----------------------------------------------------------------------
    # 7. Open Document — Microsoft Word must really open/read the document
    # -----------------------------------------------------------------------
    if ($validArtifacts.Count -gt 0) {
        $artifact = $validArtifacts[0]
        $artifactBase = [System.IO.Path]::GetFileNameWithoutExtension($artifact)
        $Results['opened_artifact'] = $artifact

        $openDocument = Find-Element -Root $active.Window -NamePattern '^Open Document$' -Type $ControlType::Button -TimeoutSeconds $UiTimeoutSeconds
        if (-not $openDocument -or -not $openDocument.Current.IsEnabled) {
            Add-Check 'open-document-enabled' $false 'Open Document button unavailable after success'
        } else {
            Add-Check 'open-document-enabled' $true 'Open Document enabled after SUCCESS'
            Add-Check 'artifact-present-before-open' (Test-Path -LiteralPath $artifact) 'artifact exists before the launcher runs'

            Click-Element -Window $active.Window -Element $openDocument
            $wordWindow = Wait-ForDesktopWindowByClass -ClassName 'OpusApp' -TitleContains $artifactBase -TimeoutSeconds $WordTimeoutSeconds
            Add-Check 'word-actually-opened' ([bool]$wordWindow) `
                $(if ($wordWindow) { "Word window '{0}'" -f $wordWindow.title } else { "no Word window for '{0}'" -f $artifactBase })
            $Results['word_window_title'] = $(if ($wordWindow) { $wordWindow.title } else { $null })

            $locked = Wait-ForExclusiveLock -Path $artifact -TimeoutSeconds 30
            Add-Check 'word-holds-exclusive-lock' ([bool]$locked) 'Word held the DOCX under an exclusive lock while displayed'

            if ($wordWindow) {
                [void][MdcInput]::PostMessage($wordWindow.handle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)  # WM_CLOSE
                $wordClosed = Wait-ForDesktopWindowGone -ClassName 'OpusApp' -TitleContains $artifactBase -TimeoutSeconds 60
                Add-Check 'word-closed-cleanly' ([bool]$wordClosed) 'Word window closed'
            }
            Add-Check 'artifact-present-after-open' (Test-Path -LiteralPath $artifact) 'artifact remains present after Word closed'
            Add-Check 'lock-released-after-word-close' (-not (Test-FileExclusivelyLocked -Path $artifact)) 'exclusive lock released'
        }
    } else {
        Add-Check 'open-document-enabled' $false 'no valid DOCX artifact to open'
    }

    # -----------------------------------------------------------------------
    # 8. Clean close
    # -----------------------------------------------------------------------
    $closed = Stop-MdcApp -App $active
    Add-Check 'clean-close' ([bool]$closed) ("process exited: {0}" -f $closed)
    $app = $null
    $appSecond = $null

    # -----------------------------------------------------------------------
    # 9. Silent uninstall
    # -----------------------------------------------------------------------
    if (-not (Test-Path -LiteralPath $Uninstaller)) {
        Add-Check 'uninstall-exit-code' $false 'unins000.exe not found'
    } else {
        $uninstallProcess = Start-Process -FilePath $Uninstaller `
            -ArgumentList '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART' -PassThru -Wait
        $Results['uninstall_exit_code'] = $uninstallProcess.ExitCode
        Add-Check 'uninstall-exit-code' ($uninstallProcess.ExitCode -eq 0) ("exit {0}" -f $uninstallProcess.ExitCode)
        Add-Check 'install-directory-removed' (-not (Test-Path -LiteralPath $InstalledExe)) 'installed executable removed'
        Add-Check 'uninstall-registry-entry-removed' (-not (Test-Path -LiteralPath $UninstallKey)) 'uninstall entry removed'
        $remainingShortcuts = @(Get-ChildItem -LiteralPath $StartMenuDir -Filter 'MD Converter*' -ErrorAction SilentlyContinue)
        Add-Check 'start-menu-entries-removed' ($remainingShortcuts.Count -eq 0) ("{0} shortcut(s) left" -f $remainingShortcuts.Count)
    }

    # -----------------------------------------------------------------------
    # 10. User data must survive uninstall
    # -----------------------------------------------------------------------
    Add-Check 'user-document-preserved' (Test-Path -LiteralPath $Sentinel) ("{0}" -f $Sentinel)
    Add-Check 'converted-document-preserved' ($validArtifacts.Count -gt 0 -and (Test-Path -LiteralPath $validArtifacts[0])) `
        ("{0}" -f $(if ($validArtifacts.Count -gt 0) { $validArtifacts[0] } else { 'n/a' }))
    Add-Check 'settings-key-preserved' (Test-Path -LiteralPath 'HKCU:\Software\MD Converter\MD Converter') 'GUI settings key still present'
}
catch {
    Add-Check 'harness' $false ("aborted: {0}" -f $_.Exception.Message)
}
finally {
    foreach ($running in @($app, $appSecond)) {
        if ($running) {
            try {
                $running.Process.Refresh()
                if (-not $running.Process.HasExited) { $running.Process.Kill() }
            } catch { }
        }
    }
    Get-Process MD_Converter -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

    # Restore the preference store exactly as it was found.
    try {
        if ($prefsExistedBefore) {
            Set-ItemProperty -Path $PrefsKey -Name 'remember' -Value "$prefsValueBefore" -ErrorAction SilentlyContinue
        } else {
            Remove-ItemProperty -Path $PrefsKey -Name 'remember' -ErrorAction SilentlyContinue
        }
    } catch { }
}

# ---------------------------------------------------------------------------
# 11. Post-smoke drift check on the frozen installer
# ---------------------------------------------------------------------------
try {
    $postHash = (Get-FileHash -LiteralPath $InstallerPath -Algorithm SHA256).Hash
    $Results['post_smoke_installer_sha256'] = $postHash
    Add-Check 'post-smoke-binary-drift-zero' ($postHash -eq $ExpectedInstallerSha256) ("{0}" -f $postHash)
} catch {
    Add-Check 'post-smoke-binary-drift-zero' $false ("hash re-read failed: {0}" -f $_.Exception.Message)
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
