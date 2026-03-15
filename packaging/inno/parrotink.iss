; Inno Setup Script for ParrotInk

#define MyAppName "ParrotInk"
#define MyAppVersion "0.2.29"
#define MyAppPublisher "Aalwattar"
#define MyAppURL "https://github.com/Aalwattar/ParrotInk"
#define MyAppExeName "ParrotInk.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
AppId={{5D0B1C4E-7F8A-4D9B-B1C2-8E3D4F5A6B7C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\{#MyAppName}
PrivilegesRequired=lowest
AppMutex=Global\ParrotInk_Mutex_2026
OutputDir=..\..\dist
OutputBaseFilename={#MyAppName}-Setup
SetupIconFile=..\..\assets\icons\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=force
CloseApplicationsFilter={#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\assets"
Type: files; Name: "{app}\{#MyAppExeName}"

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  // Graceful shutdown attempt (WM_CLOSE)
  Exec(ExpandConstant('{cmd}'), '/c taskkill /im {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

  // Brief pause to allow for cleanup
  Sleep(500);

  // Forceful shutdown (failsafe)
  // Note: We do NOT use /t here to avoid tree-kill issues with the installer process itself
  Exec(ExpandConstant('{cmd}'), '/c taskkill /f /im {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    Exec(ExpandConstant('{cmd}'), '/c taskkill /f /im {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;
