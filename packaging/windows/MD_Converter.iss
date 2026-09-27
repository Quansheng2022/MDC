#define MyAppName "MD Converter"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "Quansheng2022"

#define MyAppExeSource "MD_Converter_Lite.exe"
#define MyAppExeName "MD_Converter.exe"

#define MyAppId "MDConverter.Quansheng2022"

; ============================================================================
; MD Converter v1.1.0
; Windows Lite Distribution
;
; Program directory:
;   %LOCALAPPDATA%\Programs\MD_Converter
;
; User workspace:
;   %USERPROFILE%\Documents\MD_Converter
;       input\
;       output\
;
; Distribution profile:
;   Lite
;   Playwright / Chromium are NOT bundled.
;
; SetupArchitecture=x64 generates a 64-bit installer.
; MinVersion=10.0 restricts installation to Windows 10 or later.
; ChangesEnvironment=yes notifies Windows to refresh the environment variables.
; ============================================================================


[Setup]

; ============================================================================
; APPLICATION IDENTITY
;
; IMPORTANT:
; Keep AppId unchanged for future versions such as:
;   v1.1.1
;   v1.2.0
;   v2.0.0
;
; Inno Setup uses AppId to identify upgrades of the same application.
; ============================================================================

AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}

LicenseFile=..\..\EULA.txt

; ============================================================================
; WINDOWS REQUIREMENTS
;
; Official support:
;   Windows 10 x64
;   Windows 11 x64
;
; Windows 7 / Windows 8.x are not supported by this distribution.
; ============================================================================

MinVersion=10.0

SetupArchitecture=x64
ArchitecturesAllowed=x64compatible


; ============================================================================
; INSTALL LOCATION
;
; On the current machine:
;
; C:\Users\Quansheng\AppData\Local\Programs\MD_Converter
;
; Per-user installation:
; Administrator privileges are not required.
; ============================================================================

DefaultDirName={localappdata}\Programs\MD_Converter
DefaultGroupName=MD Converter

PrivilegesRequired=lowest


; ============================================================================
; INSTALLER USER INTERFACE
; ============================================================================

WizardStyle=modern

DisableProgramGroupPage=yes
AllowNoIcons=no

CloseApplications=yes
RestartApplications=no

UsePreviousAppDir=yes
UsePreviousTasks=yes


; ============================================================================
; UNINSTALL
; ============================================================================

Uninstallable=yes

UninstallDisplayName=MD Converter 1.1.0
UninstallDisplayIcon={app}\{#MyAppExeName}


; ============================================================================
; ENVIRONMENT VARIABLES
;
; PATH is updated by the [Code] section.
;
; ChangesEnvironment=yes tells Windows that environment variables changed.
; ============================================================================

ChangesEnvironment=yes


; ============================================================================
; INSTALLER OUTPUT
;
; Script:
;   PROJECT_ROOT\packaging\windows\MD_Converter.iss
;
; Output:
;   PROJECT_ROOT\dist_installer\
;       MD_Converter_v1.1.0_Setup.exe
; ============================================================================

OutputDir=..\..\dist_installer
OutputBaseFilename=MD_Converter_v1.1.0_Setup


; ============================================================================
; COMPRESSION
; ============================================================================

Compression=lzma2
SolidCompression=yes


; ============================================================================
; WINDOWS FILE METADATA
; ============================================================================

VersionInfoVersion=1.1.0.0
VersionInfoProductName=MD Converter
VersionInfoProductVersion=1.1.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=Markdown to Microsoft Word DOCX Converter
VersionInfoCopyright=Copyright (C) 2026 {#MyAppPublisher}


; ============================================================================
; SOURCE FILES
;
; Expected PyInstaller directory:
;
; PROJECT_ROOT\
;   dist\
;     MD_Converter_Lite\
;       MD_Converter_Lite.exe
;       _internal\
;
; MD_Converter_Lite.exe is installed as:
;
;   MD_Converter.exe
;
; The user therefore sees the normal product name rather than the
; internal packaging-profile name "Lite".
; ============================================================================

[Files]

; Main executable

Source: "..\..\dist\MD_Converter_Lite\{#MyAppExeSource}"; \
    DestDir: "{app}"; \
    DestName: "{#MyAppExeName}"; \
    Flags: ignoreversion


; PyInstaller runtime

Source: "..\..\dist\MD_Converter_Lite\_internal\*"; \
    DestDir: "{app}\_internal"; \
    Flags: ignoreversion recursesubdirs createallsubdirs


; ============================================================================
; USER WORKSPACE
;
; Normally resolves on the current machine to:
;
; C:\Users\Quansheng\Documents\MD_Converter\
;
;   input\
;   output\
;
; IMPORTANT:
;
; uninsneveruninstall ensures uninstalling MD Converter does NOT remove
; user Markdown files or generated Word documents.
; ============================================================================

[Dirs]

Name: "{userdocs}\MD_Converter"; \
    Flags: uninsneveruninstall

Name: "{userdocs}\MD_Converter\input"; \
    Flags: uninsneveruninstall

Name: "{userdocs}\MD_Converter\output"; \
    Flags: uninsneveruninstall


; ============================================================================
; OPTIONAL INSTALLATION TASKS
; ============================================================================

[Tasks]

; Add application directory to current user's PATH.
; Selected by default.

Name: "addtopath"; \
    Description: "Add MD Converter to the current user's PATH"; \
    GroupDescription: "Command-line integration:"


; Desktop shortcut is optional and not selected by default.

Name: "desktopicon"; \
    Description: "Create a desktop shortcut"; \
    GroupDescription: "Additional shortcuts:"; \
    Flags: unchecked


; ============================================================================
; SHORTCUTS
;
; IMPORTANT:
;
; WorkingDir is:
;
;   Documents\MD_Converter
;
; MD Converter currently uses relative default directories:
;
;   input
;   output
;
; Therefore when launched from these shortcuts:
;
;   input  -> Documents\MD_Converter\input
;   output -> Documents\MD_Converter\output
; ============================================================================

[Icons]


; --------------------------------------------------------------------------
; Start Menu - MD Converter
; --------------------------------------------------------------------------

Name: "{group}\MD Converter"; \
    Filename: "{app}\{#MyAppExeName}"; \
    WorkingDir: "{userdocs}\MD_Converter"


; --------------------------------------------------------------------------
; Desktop shortcut
; --------------------------------------------------------------------------

Name: "{userdesktop}\MD Converter"; \
    Filename: "{app}\{#MyAppExeName}"; \
    WorkingDir: "{userdocs}\MD_Converter"; \
    Tasks: desktopicon


; --------------------------------------------------------------------------
; Start Menu - Input Folder
; --------------------------------------------------------------------------

Name: "{group}\MD Converter - Input Folder"; \
    Filename: "{userdocs}\MD_Converter\input"


; --------------------------------------------------------------------------
; Start Menu - Output Folder
; --------------------------------------------------------------------------

Name: "{group}\MD Converter - Output Folder"; \
    Filename: "{userdocs}\MD_Converter\output"


; --------------------------------------------------------------------------
; Start Menu - Uninstall
; --------------------------------------------------------------------------

Name: "{group}\Uninstall MD Converter"; \
    Filename: "{uninstallexe}"


; ============================================================================
; POST-INSTALL ACTIONS
;
; Do NOT automatically run MD_Converter.exe without arguments.
;
; If input\ is empty, MD Converter would correctly report:
;
;   No Markdown files found
;
; Instead, optionally open the workspace after installation.
; ============================================================================

[Run]

Filename: "explorer.exe"; \
    Parameters: """{userdocs}\MD_Converter"""; \
    Description: "Open MD Converter workspace"; \
    Flags: postinstall nowait skipifsilent unchecked


; ============================================================================
; PATH MANAGEMENT
;
; The installer:
;
; 1. Adds {app} to the CURRENT USER PATH when "addtopath" is selected.
; 2. Avoids duplicate PATH entries.
; 3. Records whether this installer added the PATH entry.
; 4. Removes the PATH entry during uninstall ONLY if this installer added it.
;
; It does NOT modify the machine-wide/system PATH.
; ============================================================================

[Code]

const
  AppRegistryKey = 'Software\Quansheng2022\MD_Converter';
  PathMarkerName = 'PathAddedByInstaller';


function NormalizePathEntry(S: String): String;
begin
  S := Trim(S);
  S := RemoveQuotes(S);

  if S <> '' then
    S := RemoveBackslashUnlessRoot(S);

  Result := S;
end;


function PathContains(
  const PathValue: String;
  const Entry: String
): Boolean;

var
  Parts: TArrayOfString;
  I: Integer;
  Candidate: String;
  NormalizedEntry: String;

begin
  Result := False;

  NormalizedEntry := NormalizePathEntry(Entry);

  if NormalizedEntry = '' then
    Exit;

  // The parameter list is kept on one line: a continuation line that starts
  // with "[" is parsed by Inno Setup as a new section tag ("Invalid section
  // tag"), so the array-of-string literal must not begin a line.
  Parts := StringSplit(PathValue, [';'], stExcludeEmpty);

  if GetArrayLength(Parts) = 0 then
    Exit;

  for I := 0 to GetArrayLength(Parts) - 1 do
  begin

    Candidate := NormalizePathEntry(Parts[I]);

    if SameText(
      Candidate,
      NormalizedEntry
    ) then
    begin

      Result := True;
      Exit;

    end;

  end;

end;


procedure AddToUserPath;

var
  ExistingPath: String;
  NewPath: String;
  AppPath: String;

begin

  AppPath := ExpandConstant('{app}');

  ExistingPath := '';

  RegQueryStringValue(
    HKCU,
    'Environment',
    'Path',
    ExistingPath
  );


  if PathContains(
    ExistingPath,
    AppPath
  ) then
  begin

    Log(
      'MD Converter PATH entry already exists: ' +
      AppPath
    );

    Exit;

  end;


  if ExistingPath = '' then
  begin

    NewPath := AppPath;

  end
  else
  begin

    NewPath :=
      ExistingPath +
      ';' +
      AppPath;

  end;


  if RegWriteExpandStringValue(
    HKCU,
    'Environment',
    'Path',
    NewPath
  ) then
  begin

    Log(
      'Added MD Converter to current user PATH: ' +
      AppPath
    );


    RegWriteDWordValue(
      HKCU,
      AppRegistryKey,
      PathMarkerName,
      1
    );

  end
  else
  begin

    Log(
      'WARNING: Failed to update current user PATH.'
    );

  end;

end;


function RemovePathEntry(
  const PathValue: String;
  const Entry: String
): String;

var
  Parts: TArrayOfString;
  KeptParts: TArrayOfString;

  I: Integer;
  Count: Integer;

  Candidate: String;
  NormalizedEntry: String;

begin

  NormalizedEntry :=
    NormalizePathEntry(Entry);


  Parts := StringSplit(PathValue, [';'], stExcludeEmpty);


  if GetArrayLength(Parts) = 0 then
  begin

    Result := '';
    Exit;

  end;


  SetArrayLength(
    KeptParts,
    GetArrayLength(Parts)
  );


  Count := 0;


  for I := 0 to GetArrayLength(Parts) - 1 do
  begin

    Candidate :=
      NormalizePathEntry(
        Parts[I]
      );


    if not SameText(
      Candidate,
      NormalizedEntry
    ) then
    begin

      KeptParts[Count] :=
        Trim(Parts[I]);

      Count := Count + 1;

    end;

  end;


  SetArrayLength(
    KeptParts,
    Count
  );


  Result :=
    StringJoin(
      ';',
      KeptParts
    );

end;


procedure RemoveFromUserPath;

var
  ExistingPath: String;
  NewPath: String;

  AppPath: String;

  Marker: Cardinal;

begin

  Marker := 0;


  // Only remove PATH if THIS installer added it.

  if not RegQueryDWordValue(
    HKCU,
    AppRegistryKey,
    PathMarkerName,
    Marker
  ) then
  begin

    Log(
      'No installer PATH marker found. PATH will not be modified.'
    );

    Exit;

  end;


  if Marker <> 1 then
    Exit;


  ExistingPath := '';


  if not RegQueryStringValue(
    HKCU,
    'Environment',
    'Path',
    ExistingPath
  ) then
  begin

    Exit;

  end;


  AppPath :=
    ExpandConstant('{app}');


  NewPath :=
    RemovePathEntry(
      ExistingPath,
      AppPath
    );


  if RegWriteExpandStringValue(
    HKCU,
    'Environment',
    'Path',
    NewPath
  ) then
  begin

    Log(
      'Removed MD Converter from current user PATH: ' +
      AppPath
    );


    RegDeleteValue(
      HKCU,
      AppRegistryKey,
      PathMarkerName
    );


    RegDeleteKeyIfEmpty(
      HKCU,
      AppRegistryKey
    );

  end;

end;


procedure CurStepChanged(
  CurStep: TSetupStep
);

begin

  if CurStep = ssPostInstall then
  begin

    if WizardIsTaskSelected('addtopath') then
    begin

      AddToUserPath;

    end;

  end;

end;


procedure CurUninstallStepChanged(
  CurUninstallStep: TUninstallStep
);

begin

  if CurUninstallStep = usPostUninstall then
  begin

    RemoveFromUserPath;

  end;

end;
