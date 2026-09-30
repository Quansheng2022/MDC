#requires -Version 5.1
<#
.SYNOPSIS
    Install / launch / convert / uninstall / reinstall lifecycle verifier for
    R2-PRE-RC-01 (WP-03).

.DESCRIPTION
    Verification tooling only. It drives the *final rebuilt* Inno Setup installer
    through a real Windows lifecycle and records machine-readable observations.
    Phases: PRE (pre-state snapshot), INSTALL (clean-state preparation plus silent
    install), LAUNCH (installed product launch and runtime independence), CONVERT
    (representative Markdown -> DOCX conversion), UNINSTALL, REINSTALL, CONVERT2
    (short post-reinstall smoke).

    Every conversion goes through the product's own GUI path
    (GUI -> GuiWorker -> ConversionService -> Canonical Core) using the shared
    automation helpers in tools/packaging/gui_automation.ps1. No product logic is
    reimplemented and no product file is modified.

.EXAMPLE
    powershell -File r2prerc01_lifecycle.ps1 -Phase PRE -WorkRoot C:\temp\mdc_pre_rc_01
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('PRE', 'INSTALL', 'LAUNCH', 'CONVERT', 'UNINSTALL', 'REINSTALL', 'CONVERT2', 'FINAL')]
    [string]$Phase,

    [Parameter(Mandatory = $true)]
    [string]$WorkRoot,

    [string]$InstallerPath,
    [int]$StartupTimeoutSeconds = 120,
    [int]$UiTimeoutSeconds = 45,
    [int]$ConversionTimeoutSeconds = 600
)

$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..\..')).Path
. (Join-Path $RepoRoot 'tools\packaging\gui_automation.ps1')

if (-not $InstallerPath) {
    $InstallerPath = Join-Path $RepoRoot 'dist_installer\MD_Converter_v1.1.0_Setup.exe'
}

# Frozen accepted payload identity (WP-R2PRERC01-01).
$ExpectedPayloadExe = '68524527CDC5718CE31A1F0454EAFB0FF64C52D5C838716AC1277445DE0E3021'
# Frozen final installer identity (WP-R2PRERC01-02).
$ExpectedInstaller = '4B56FC989BAB7FF7E648CC29DFE5A6D944B2B8EFC420F11DE8D0ECF8294FFDE9'

$InstallRoot = Join-Path $env:LOCALAPPDATA 'Programs\MD_Converter'
$InstalledExe = Join-Path $InstallRoot 'MD_Converter.exe'
$Uninstaller = Join-Path $InstallRoot 'unins000.exe'
$UserWorkspace = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'MD_Converter'
$StartMenuGroup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\MD Converter'
$DesktopShortcut = Join-Path ([Environment]::GetFolderPath('Desktop')) 'MD Converter.lnk'
$PathMarkerKey = 'HKCU:\Software\Quansheng2022\MD_Converter'
$MainWindowTitle = 'MD Converter'

$FixtureDir = Join-Path $RepoRoot 'Doc\V2\Implementation\R2_PRE_RC_01\Verification\fixtures'
$ResultsDir = Join-Path $WorkRoot 'results'
$LogDir = Join-Path $WorkRoot 'logs'
$Cwd1 = Join-Path $WorkRoot 'cwd_representative'
$Cwd2 = Join-Path $WorkRoot 'cwd_short'

function Initialize-Directories {
    foreach ($path in @($WorkRoot, $ResultsDir, $LogDir, $Cwd1, $Cwd2)) {
        if (-not (Test-Path -LiteralPath $path)) { New-Item -ItemType Directory -Path $path -Force | Out-Null }
    }
}

function Save-Result {
    param([string]$Name, [System.Collections.IDictionary]$Payload)
    Initialize-Directories
    $path = Join-Path $ResultsDir ("$Name.json")
    $Payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $path -Encoding UTF8
    Write-Host ("result written: {0}" -f $path)
}

function Get-Sha256 {
    param([string]$LiteralPath)
    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash
}

function Get-UserPathValue {
    try {
        $item = Get-ItemProperty -LiteralPath 'HKCU:\Environment' -Name 'Path' -ErrorAction Stop
        return [string]$item.Path
    } catch {
        return ''
    }
}

function Get-MdConverterUninstallEntry {
    $roots = @(
        'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
    )
    foreach ($root in $roots) {
        $found = @(Get-ItemProperty -Path $root -ErrorAction SilentlyContinue |
            Where-Object { $_.DisplayName -like '*MD Converter*' })
        if ($found.Count -gt 0) { return $found }
    }
    return @()
}

function Stop-InstalledApp {
    $stopped = @()
    foreach ($process in @(Get-Process -Name 'MD_Converter' -ErrorAction SilentlyContinue)) {
        try { $process.CloseMainWindow() | Out-Null } catch { }
    }
    Start-Sleep -Seconds 2
    foreach ($process in @(Get-Process -Name 'MD_Converter' -ErrorAction SilentlyContinue)) {
        $stopped += $process.Id
        try { $process.Kill() } catch { }
    }
    return $stopped
}

function Invoke-SilentSetup {
    param([string]$LogName)
    $log = Join-Path $LogDir $LogName
    $arguments = @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-', "/LOG=$log")
    $process = Start-Process -FilePath $InstallerPath -ArgumentList $arguments -Wait -PassThru
    return [ordered]@{ exit_code = $process.ExitCode; log = $log }
}

function Use-SanitizedEnvironment {
    foreach ($name in @('PYTHONPATH', 'PYTHONHOME')) {
        Remove-Item -LiteralPath ("Env:{0}" -f $name) -ErrorAction SilentlyContinue
    }
    $env:PATH = (($env:PATH -split ';' | Where-Object {
        $entry = $_.Trim().Trim('"')
        $entry -and ($entry -notlike "$RepoRoot*") -and ($entry -notlike '*\.venv\*')
    }) -join ';')
}

function Get-InstallArtifactSnapshot {
    $exeExists = Test-Path -LiteralPath $InstalledExe
    $exeHash = $null
    $internalCount = 0
    if ($exeExists) { $exeHash = Get-Sha256 -LiteralPath $InstalledExe }
    $internalDir = Join-Path $InstallRoot '_internal'
    if (Test-Path -LiteralPath $internalDir) {
        $internalCount = @(Get-ChildItem -LiteralPath $internalDir -Recurse -File).Count
    }
    $shortcuts = @()
    if (Test-Path -LiteralPath $StartMenuGroup) {
        $shortcuts = @(Get-ChildItem -LiteralPath $StartMenuGroup -Filter '*.lnk' -File |
            ForEach-Object { $_.Name })
    }
    $userPath = Get-UserPathValue
    $marker = $null
    if (Test-Path -LiteralPath $PathMarkerKey) {
        $marker = (Get-ItemProperty -LiteralPath $PathMarkerKey -Name 'PathAddedByInstaller' -ErrorAction SilentlyContinue).PathAddedByInstaller
    }
    $pathHasApp = @(($userPath -split ';') | Where-Object {
        $entry = $_.Trim().Trim('"').TrimEnd('\')
        $entry -and ($entry -ieq $InstallRoot.TrimEnd('\'))
    }).Count -gt 0
    return [ordered]@{
        install_root                  = $InstallRoot
        install_root_exists           = (Test-Path -LiteralPath $InstallRoot)
        installed_exe_exists          = $exeExists
        installed_exe_sha256          = $exeHash
        installed_exe_matches_payload = ($exeHash -eq $ExpectedPayloadExe)
        internal_file_count           = $internalCount
        eula_present                  = (Test-Path -LiteralPath (Join-Path $InstallRoot 'EULA.txt'))
        third_party_notices_present   = (Test-Path -LiteralPath (Join-Path $InstallRoot 'THIRD_PARTY_NOTICES.txt'))
        start_menu_group_present      = (Test-Path -LiteralPath $StartMenuGroup)
        start_menu_shortcuts          = $shortcuts
        desktop_shortcut_present      = (Test-Path -LiteralPath $DesktopShortcut)
        uninstaller_present           = (Test-Path -LiteralPath $Uninstaller)
        uninstall_entries             = @(Get-MdConverterUninstallEntry | ForEach-Object {
                [ordered]@{
                    display_name     = $_.DisplayName
                    display_version  = $_.DisplayVersion
                    publisher        = $_.Publisher
                    install_location = $_.InstallLocation
                    uninstall_string = $_.UninstallString
                    display_icon     = $_.DisplayIcon
                }
            })
        user_path_contains_app        = $pathHasApp
        user_path_marker              = $marker
        user_workspace_input_present  = (Test-Path -LiteralPath (Join-Path $UserWorkspace 'input'))
        user_workspace_output_present = (Test-Path -LiteralPath (Join-Path $UserWorkspace 'output'))
    }
}

function Test-AllChecksPassed {
    param([System.Collections.IDictionary]$Checks, [string[]]$IgnoreKeys = @())
    foreach ($key in $Checks.Keys) {
        if ($IgnoreKeys -contains $key) { continue }
        if (-not $Checks[$key]) { return $false }
    }
    return $true
}

switch ($Phase) {

    'PRE' {
        Initialize-Directories
        $result = [ordered]@{
            phase                       = 'PRE'
            captured_at                 = (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz')
            repository_root             = $RepoRoot
            work_root                   = $WorkRoot
            installer_path              = $InstallerPath
            installer_exists            = (Test-Path -LiteralPath $InstallerPath)
            installer_sha256            = $(if (Test-Path -LiteralPath $InstallerPath) { Get-Sha256 -LiteralPath $InstallerPath } else { $null })
            expected_installer_sha256   = $ExpectedInstaller
            expected_payload_exe_sha256 = $ExpectedPayloadExe
            fixture_representative      = (Join-Path $FixtureDir 'representative.md')
            fixture_short               = (Join-Path $FixtureDir 'short.md')
            running_app_processes       = @(Get-Process -Name 'MD_Converter' -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
            pre_install                 = (Get-InstallArtifactSnapshot)
            user_path_value             = (Get-UserPathValue)
        }
        Save-Result -Name 'phase_PRE' -Payload $result
        Write-Host ("installer sha256 matches frozen : {0}" -f ($result.installer_sha256 -eq $ExpectedInstaller))
        Write-Host ("pre-install install_root_exists : {0}" -f $result.pre_install.install_root_exists)
    }

    'INSTALL' {
        Initialize-Directories
        if (-not (Test-Path -LiteralPath $InstallerPath)) { throw "installer missing: $InstallerPath" }
        $installerHash = Get-Sha256 -LiteralPath $InstallerPath
        if ($installerHash -ne $ExpectedInstaller) { throw "installer identity changed: $installerHash" }
        $stoppedProcesses = Stop-InstalledApp
        $expectedRoot = Join-Path $env:LOCALAPPDATA 'Programs\MD_Converter'
        $removedPriorInstall = $false
        if (Test-Path -LiteralPath $InstallRoot) {
            if ($InstallRoot -ne $expectedRoot) { throw "refusing to remove unexpected path: $InstallRoot" }
            Remove-Item -LiteralPath $InstallRoot -Recurse -Force
            $removedPriorInstall = -not (Test-Path -LiteralPath $InstallRoot)
        }
        $setup = Invoke-SilentSetup -LogName 'install_1.log'
        Start-Sleep -Seconds 3
        $snapshot = Get-InstallArtifactSnapshot
        $checks = [ordered]@{
            prior_install_removed    = $removedPriorInstall
            setup_exit_code_zero     = ($setup.exit_code -eq 0)
            install_root_exists      = $snapshot.install_root_exists
            installed_exe_exists     = $snapshot.installed_exe_exists
            installed_exe_matches    = $snapshot.installed_exe_matches_payload
            internal_payload_present = ($snapshot.internal_file_count -gt 0)
            compliance_docs_present  = ($snapshot.eula_present -and $snapshot.third_party_notices_present)
            start_menu_group_present = $snapshot.start_menu_group_present
            uninstall_registered     = ($snapshot.uninstall_entries.Count -gt 0)
            uninstaller_present      = $snapshot.uninstaller_present
            user_path_entry_present  = $snapshot.user_path_contains_app
            user_workspace_created   = ($snapshot.user_workspace_input_present -and $snapshot.user_workspace_output_present)
            desktop_shortcut_absent  = (-not $snapshot.desktop_shortcut_present)
        }
        $result = [ordered]@{
            phase             = 'INSTALL'
            captured_at       = (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz')
            installer_sha256  = $installerHash
            prior_install_dir = $InstallRoot
            stopped_processes = @($stoppedProcesses)
            setup             = $setup
            snapshot          = $snapshot
            checks            = $checks
            status            = $(if (Test-AllChecksPassed -Checks $checks) { 'PASS' } else { 'FAIL' })
        }
        Save-Result -Name 'phase_INSTALL' -Payload $result
        foreach ($key in $checks.Keys) { Write-Host ("  {0,-26} : {1}" -f $key, $checks[$key]) }
        Write-Host ("INSTALL : {0}" -f $result.status)
    }

    'LAUNCH' {
        Initialize-Directories
        if (-not (Test-Path -LiteralPath $InstalledExe)) { throw "installed executable missing: $InstalledExe" }
        Use-SanitizedEnvironment
        $process = Start-Process -FilePath $InstalledExe -WorkingDirectory $Cwd1 -PassThru
        $appProcessId = $process.Id
        $window = Get-TopLevelWindow -ProcessId $appProcessId -Name $MainWindowTitle -TimeoutSeconds $StartupTimeoutSeconds
        $moduleCount = 0
        $moduleHits = @()
        $moduleError = $null
        if ($window) {
            Start-Sleep -Seconds 2
            try {
                $modules = @($process.Modules | ForEach-Object { $_.FileName })
                $moduleCount = $modules.Count
                $moduleHits = @($modules | Where-Object { $_ -like "$RepoRoot*" -or $_ -like '*\.venv\*' })
            } catch {
                $moduleError = $_.Exception.Message
            }
        }
        $closedCleanly = $false
        if ($window) {
            Close-WindowElement -Element $window
            $deadline = (Get-Date).AddSeconds(30)
            while ((Get-Date) -lt $deadline) {
                $process.Refresh()
                if ($process.HasExited) { break }
                Start-Sleep -Milliseconds 400
            }
            $process.Refresh()
            $closedCleanly = [bool]$process.HasExited
        }
        if (-not $process.HasExited) { try { $process.Kill() } catch { } }
        $pathEntries = @($env:PATH -split ';' | ForEach-Object { $_.Trim().Trim('"') })
        $checks = [ordered]@{
            main_window_visible                  = [bool]$window
            pythonpath_empty                     = [string]::IsNullOrEmpty($env:PYTHONPATH)
            repository_absent_from_child_path    = (@($pathEntries | Where-Object { $_ -like "$RepoRoot*" }).Count -eq 0)
            dotvenv_absent_from_child_path       = (@($pathEntries | Where-Object { $_ -like '*\.venv\*' }).Count -eq 0)
            no_repository_or_venv_modules_loaded = ($moduleHits.Count -eq 0)
            clean_close                          = $closedCleanly
        }
        $result = [ordered]@{
            phase                = 'LAUNCH'
            captured_at          = (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz')
            installed_exe        = $InstalledExe
            installed_exe_sha256 = (Get-Sha256 -LiteralPath $InstalledExe)
            process_id           = $appProcessId
            working_directory    = $Cwd1
            window_title         = $(if ($window) { $window.Current.Name } else { $null })
            child_pythonpath     = [string]$env:PYTHONPATH
            child_path_entries   = @($pathEntries).Count
            module_count         = $moduleCount
            repository_or_venv_module_hits = @($moduleHits)
            module_enumeration_error = $moduleError
            checks               = $checks
            status               = $(if (Test-AllChecksPassed -Checks $checks) { 'PASS' } else { 'FAIL' })
        }
        Save-Result -Name 'phase_LAUNCH' -Payload $result
        foreach ($key in $checks.Keys) { Write-Host ("  {0,-38} : {1}" -f $key, $checks[$key]) }
        Write-Host ("LAUNCH : {0}" -f $result.status)
    }

    { $_ -in 'CONVERT', 'CONVERT2' } {
        Initialize-Directories
        $fixture = if ($Phase -eq 'CONVERT') { Join-Path $FixtureDir 'representative.md' } else { Join-Path $FixtureDir 'short.md' }
        $workDir = if ($Phase -eq 'CONVERT') { $Cwd1 } else { $Cwd2 }
        if (-not (Test-Path -LiteralPath $fixture)) { throw "fixture missing: $fixture" }
        Use-SanitizedEnvironment
        $evidenceJson = Join-Path $LogDir ("gui_smoke_{0}.json" -f $Phase.ToLowerInvariant())
        & (Join-Path $RepoRoot 'tools\packaging\windows_gui_smoke.ps1') `
            -ExePath $InstalledExe `
            -InputMarkdown $fixture `
            -WorkDir $workDir `
            -EvidencePath $evidenceJson `
            -StartupTimeoutSeconds $StartupTimeoutSeconds `
            -UiTimeoutSeconds $UiTimeoutSeconds `
            -ConversionTimeoutSeconds $ConversionTimeoutSeconds
        $smokeExit = $LASTEXITCODE
        $smoke = Get-Content -LiteralPath $evidenceJson -Raw -Encoding UTF8 | ConvertFrom-Json
        $stem = [System.IO.Path]::GetFileNameWithoutExtension($fixture)
        $outputDir = Join-Path $workDir 'output'
        # Naming rule exercised here: the representative fixture declares a
        # frontmatter title, so the artifact is named from that title; the short
        # post-reinstall fixture has no frontmatter, so the name derives from the
        # source stem.
        $expectedName = if ($Phase -eq 'CONVERT') {
            'MD_Converter_R2_Pre-RC_Installer_Verification.docx'
        } else {
            "$stem.docx"
        }
        $expectedDocx = Join-Path $outputDir $expectedName
        $expectedDocxPresent = Test-Path -LiteralPath $expectedDocx
        $outputDirArtifacts = @()
        if (Test-Path -LiteralPath $outputDir) {
            $outputDirArtifacts = @(Get-ChildItem -LiteralPath $outputDir -Filter '*.docx' -File |
                ForEach-Object { $_.Name })
        }
        $docxInfo = $null
        if ($expectedDocxPresent) {
            $item = Get-Item -LiteralPath $expectedDocx
            $docxInfo = [ordered]@{
                path       = $expectedDocx
                bytes      = $item.Length
                sha256     = (Get-Sha256 -LiteralPath $expectedDocx)
                last_write = $item.LastWriteTime.ToString('o')
            }
        }
        $checks = [ordered]@{
            smoke_harness_exit_zero      = ($smokeExit -eq 0)
            smoke_harness_status_pass    = ($smoke.status -eq 'PASS')
            file_selected                = [bool]$smoke.'select-file'.passed
            convert_enabled              = [bool]$smoke.'convert-enabled'.passed
            conversion_reached_success   = ($smoke.conversion_outcome.outcome -eq 'SUCCESS')
            docx_valid                   = [bool]$smoke.'docx-valid'.passed
            expected_output_name_present = $expectedDocxPresent
            single_output_artifact       = ($outputDirArtifacts.Count -eq 1)
            clean_close                  = [bool]$smoke.'clean-close'.passed
        }
        $result = [ordered]@{
            phase            = $Phase
            captured_at      = (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz')
            installed_exe    = $InstalledExe
            fixture          = $fixture
            work_directory   = $workDir
            expected_docx    = $expectedDocx
            expected_output_name = $expectedName
            output_directory = $outputDir
            output_dir_artifacts = @($outputDirArtifacts)
            docx             = $docxInfo
            smoke_evidence   = $evidenceJson
            smoke_summary    = [ordered]@{
                status          = $smoke.status
                conversion      = $smoke.conversion_outcome
                artifacts       = @($smoke.docx_artifacts)
                valid_artifacts = @($smoke.valid_docx_artifacts)
                failed_checks   = @($smoke.failed_checks)
            }
            checks           = $checks
            status           = $(if (Test-AllChecksPassed -Checks $checks) { 'PASS' } else { 'FAIL' })
        }
        Save-Result -Name ("phase_{0}" -f $Phase) -Payload $result
        foreach ($key in $checks.Keys) { Write-Host ("  {0,-30} : {1}" -f $key, $checks[$key]) }
        Write-Host ("{0} : {1}" -f $Phase, $result.status)
    }

    'UNINSTALL' {
        Initialize-Directories
        $stoppedProcesses = Stop-InstalledApp
        if (-not (Test-Path -LiteralPath $Uninstaller)) { throw "uninstaller missing: $Uninstaller" }
        $before = Get-InstallArtifactSnapshot
        $preStatePath = Join-Path $ResultsDir 'phase_PRE.json'
        $preUserPath = $null
        if (Test-Path -LiteralPath $preStatePath) {
            $preUserPath = (Get-Content -LiteralPath $preStatePath -Raw -Encoding UTF8 | ConvertFrom-Json).user_path_value
        }
        $postUserPath = Get-UserPathValue
        $uninstallerHash = Get-Sha256 -LiteralPath $Uninstaller
        $process = Start-Process -FilePath $Uninstaller -ArgumentList @(
            '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'
        ) -Wait -PassThru
        $exitCode = $process.ExitCode
        $deadline = (Get-Date).AddSeconds(120)
        while ((Get-Date) -lt $deadline) {
            if (-not (Test-Path -LiteralPath $InstalledExe)) { break }
            Start-Sleep -Milliseconds 500
        }
        Start-Sleep -Seconds 3
        $after = Get-InstallArtifactSnapshot
        $checks = [ordered]@{
            uninstall_exit_code_zero       = ($exitCode -eq 0)
            installed_exe_removed          = (-not $after.installed_exe_exists)
            internal_payload_removed       = ($after.internal_file_count -eq 0)
            start_menu_group_removed       = (-not $after.start_menu_group_present)
            uninstall_registration_removed = ($after.uninstall_entries.Count -eq 0)
            user_path_neutral_cycle        = (((Get-UserPathValue)) -eq $preUserPath)
            user_path_marker_removed       = ($null -eq $after.user_path_marker)
            user_workspace_preserved       = ($after.user_workspace_input_present -and $after.user_workspace_output_present)
        }
        $result = [ordered]@{
            phase              = 'UNINSTALL'
            captured_at        = (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz')
            stopped_processes  = @($stoppedProcesses)
            uninstaller        = $Uninstaller
            uninstaller_sha256 = $uninstallerHash
            exit_code          = $exitCode
            user_path_pre_install        = $preUserPath
            user_path_before_uninstall   = $postUserPath
            user_path_after_uninstall    = (Get-UserPathValue)
            path_marker_before_uninstall = $before.user_path_marker
            before             = $before
            after              = $after
            checks             = $checks
            status             = $(if (Test-AllChecksPassed -Checks $checks) { 'PASS' } else { 'FAIL' })
        }
        Save-Result -Name 'phase_UNINSTALL' -Payload $result
        foreach ($key in $checks.Keys) { Write-Host ("  {0,-32} : {1}" -f $key, $checks[$key]) }
        Write-Host ("UNINSTALL : {0}" -f $result.status)
    }

    'REINSTALL' {
        Initialize-Directories
        $installerHash = Get-Sha256 -LiteralPath $InstallerPath
        if ($installerHash -ne $ExpectedInstaller) { throw "installer identity changed: $installerHash" }
        $setup = Invoke-SilentSetup -LogName 'install_2.log'
        Start-Sleep -Seconds 3
        $snapshot = Get-InstallArtifactSnapshot
        $checks = [ordered]@{
            setup_exit_code_zero     = ($setup.exit_code -eq 0)
            install_root_exists      = $snapshot.install_root_exists
            installed_exe_matches    = $snapshot.installed_exe_matches_payload
            internal_payload_present = ($snapshot.internal_file_count -gt 0)
            uninstall_registered     = ($snapshot.uninstall_entries.Count -gt 0)
            uninstaller_present      = $snapshot.uninstaller_present
            user_path_entry_present  = $snapshot.user_path_contains_app
        }
        $result = [ordered]@{
            phase            = 'REINSTALL'
            captured_at      = (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz')
            installer_sha256 = $installerHash
            setup            = $setup
            snapshot         = $snapshot
            checks           = $checks
            status           = $(if (Test-AllChecksPassed -Checks $checks) { 'PASS' } else { 'FAIL' })
        }
        Save-Result -Name 'phase_REINSTALL' -Payload $result
        foreach ($key in $checks.Keys) { Write-Host ("  {0,-26} : {1}" -f $key, $checks[$key]) }
        Write-Host ("REINSTALL : {0}" -f $result.status)
    }

    'FINAL' {
        Initialize-Directories
        $phaseNames = @('PRE', 'INSTALL', 'LAUNCH', 'CONVERT', 'UNINSTALL', 'REINSTALL', 'CONVERT2')
        $phaseResults = [ordered]@{}
        $phaseStatus = [ordered]@{}
        foreach ($name in $phaseNames) {
            $file = Join-Path $ResultsDir ("phase_{0}.json" -f $name)
            if (-not (Test-Path -LiteralPath $file)) { $phaseResults[$name] = $null; $phaseStatus[$name] = 'MISSING'; continue }
            $data = Get-Content -LiteralPath $file -Raw -Encoding UTF8 | ConvertFrom-Json
            $phaseResults[$name] = $data
            $phaseStatus[$name] = $(if ($data.PSObject.Properties.Name -contains 'status') { $data.status } else { 'OBSERVED' })
        }
        $failedPhases = @($phaseStatus.GetEnumerator() | Where-Object { $_.Value -notin @('PASS', 'OBSERVED') } | ForEach-Object { $_.Key })

        $productDiff = @(& git -C $RepoRoot diff --numstat -- md_converter) | Where-Object { $_ -match '\S' }
        $productDriftFiles = @()
        foreach ($line in $productDiff) {
            $parts = ($line -split "`t")
            if ($parts.Count -ge 3) { $productDriftFiles += [ordered]@{ file = $parts[2]; added = $parts[0]; removed = $parts[1] } }
        }
        # Dirty files inherited from before this gate (recorded in the R2
        # pre-RC product specification section 7) are not task-caused drift.
        $knownPreExistingDrift = @('md_converter/cli.py', 'README.md', '.gitignore')
        $introducedDrift = @($productDriftFiles | Where-Object { $knownPreExistingDrift -notcontains $_.file })
        $goldenPath = Join-Path $RepoRoot 'md_converter\tests\golden\sample.expected.json'
        $goldenHash = Get-Sha256 -LiteralPath $goldenPath
        $rcBranches = @(& git -C $RepoRoot branch --list '*rc*')
        $rcTags = @(& git -C $RepoRoot tag --list '*rc*')

        $evidenceDir = Join-Path $RepoRoot 'Doc\V2\Implementation\R2_PRE_RC_01\Evidence\lifecycle'
        if (-not (Test-Path -LiteralPath $evidenceDir)) { New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null }
        $copied = @()
        foreach ($name in $phaseNames) {
            $source = Join-Path $ResultsDir ("phase_{0}.json" -f $name)
            if (Test-Path -LiteralPath $source) {
                Copy-Item -LiteralPath $source -Destination (Join-Path $evidenceDir ("phase_{0}.json" -f $name)) -Force
                $copied += ("phase_{0}.json" -f $name)
            }
        }
        foreach ($name in @('gui_smoke_convert.json', 'gui_smoke_convert2.json')) {
            $source = Join-Path $LogDir $name
            if (Test-Path -LiteralPath $source) {
                Copy-Item -LiteralPath $source -Destination (Join-Path $evidenceDir $name) -Force
                $copied += $name
            }
        }

        $summary = [ordered]@{
            phase                        = 'FINAL'
            captured_at                  = (Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz')
            work_root                    = $WorkRoot
            installer_sha256             = $(if (Test-Path -LiteralPath $InstallerPath) { Get-Sha256 -LiteralPath $InstallerPath } else { $null })
            installed_exe_sha256         = $(if (Test-Path -LiteralPath $InstalledExe) { Get-Sha256 -LiteralPath $InstalledExe } else { $null })
            expected_payload_exe_sha256  = $ExpectedPayloadExe
            phase_status                 = $phaseStatus
            clean_install                = $phaseStatus['INSTALL']
            launch                       = $phaseStatus['LAUNCH']
            first_conversion             = $phaseStatus['CONVERT']
            uninstall                    = $phaseStatus['UNINSTALL']
            reinstall                    = $phaseStatus['REINSTALL']
            post_reinstall_smoke         = $phaseStatus['CONVERT2']
            introduced_installer_failures = $failedPhases.Count
            failed_phases                = @($failedPhases)
            unresolved_installer_blockers = $failedPhases.Count
            product_source_drift_observed = $productDriftFiles.Count
            product_source_drift_files   = @($productDriftFiles)
            pre_existing_drift_files     = @($productDriftFiles | Where-Object { $knownPreExistingDrift -contains $_.file } | ForEach-Object { $_.file })
            introduced_product_source_drift = $introducedDrift.Count
            introduced_product_source_drift_files = @($introducedDrift | ForEach-Object { $_.file })
            golden_baseline_path         = $goldenPath
            golden_baseline_sha256       = $goldenHash
            golden_baseline_unchanged    = ($goldenHash -eq '6D589013B8024C158DE5D29B93BDFEF68F2F406045C805DAB61F8E513725829A')
            converted_documents          = @(
                $phaseResults['CONVERT'].docx
                $phaseResults['CONVERT2'].docx
            )
            r2_rc_branches               = @($rcBranches)
            r2_rc_tags                   = @($rcTags)
            r2_rc_started                = (($rcBranches + $rcTags).Count -gt 0)
            evidence_files_copied        = @($copied)
            installed_state_after_gate   = [ordered]@{
                install_root_exists  = (Test-Path -LiteralPath $InstallRoot)
                installed_exe_exists = (Test-Path -LiteralPath $InstalledExe)
                uninstall_registered = (@(Get-MdConverterUninstallEntry).Count -gt 0)
            }
            result                       = $(if ($failedPhases.Count -eq 0 -and $introducedDrift.Count -eq 0) { 'PASS' } else { 'FAIL' })
        }
        Save-Result -Name 'WP-R2PRERC01-03_LIFECYCLE_RESULT' -Payload $summary
        $target = Join-Path (Join-Path $RepoRoot 'Doc\V2\Implementation\R2_PRE_RC_01\Evidence') 'WP-R2PRERC01-03_LIFECYCLE_RESULT.json'
        $summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $target -Encoding UTF8
        Write-Host ("phase status : {0}" -f (($phaseStatus.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join ', '))
        Write-Host ("result       : {0}" -f $summary.result)
    }
}
