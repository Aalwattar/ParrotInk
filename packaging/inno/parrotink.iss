; Inno Setup Script for ParrotInk

#define MyAppName "ParrotInk"
#define MyAppVersion "0.2.30"
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
; AppMutex removed to prevent silent installer from aborting if app hasn't fully closed
OutputDir=..\..\dist
OutputBaseFilename={#MyAppName}-Setup
SetupIconFile=..\..\assets\icons\icon.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=force
CloseApplicationsFilter={#MyAppExeName}
RestartApplications=no

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
; Normal install: User sees the checkbox to launch the app
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
; Silent install (updates): Force launch automatically because the wizard pages are hidden
Filename: "{app}\{#MyAppExeName}"; Flags: nowait; Check: WizardSilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\assets"
Type: files; Name: "{app}\{#MyAppExeName}"

[Code]
const
  SYNCHRONIZE = $00100000;
  INFINITE = $FFFFFFFF;

function OpenProcess(dwAccess: DWORD; bInherit: Boolean; dwPID: DWORD): THandle;
  external 'OpenProcess@kernel32.dll stdcall';
function WaitForSingleObject(hHandle: THandle; dwMilliseconds: DWORD): DWORD;
  external 'WaitForSingleObject@kernel32.dll stdcall';
function CloseHandle(hObject: THandle): Boolean;
  external 'CloseHandle@kernel32.dll stdcall';

function InitializeSetup(): Boolean;
var
  PID: Cardinal;
  Handle: THandle;
  WaitResult: DWORD;
  ResultCode: Integer;
begin
  Result := True;

  // Get PID from command line parameter /pid=xxxx
  PID := StrToIntDef(ExpandConstant('{param:pid|0}'), 0);

  if PID <> 0 then
  begin
    Log(Format('Installer received PID: %d. Attempting deterministic wait...', [PID]));

    Handle := OpenProcess(SYNCHRONIZE, False, PID);
    if Handle <> 0 then
    begin
      WaitResult := WaitForSingleObject(Handle, 20000); // 20s hard ceiling
      CloseHandle(Handle);

      if WaitResult <> 0 then
      begin
        // WAIT_OBJECT_0 is 0. Anything else (timeout/error) means process is still alive.
        Log('Wait timed out or failed. Falling back to force-kill.');
        Exec(ExpandConstant('{sys}\taskkill.exe'), '/f /im {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
        Sleep(2000); // Longer buffer post-force-kill for AV/OS cleanup
      end else
      begin
        Log('Process exited gracefully.');
        Sleep(1500); // Normal exit buffer for _MEI cleanup + AV scan latency
      end;
    end else
    begin
      // OpenProcess failed (Access Denied or PID already gone)
      Log('OpenProcess failed. Using fallback kill logic.');
      Sleep(1000);
      Exec(ExpandConstant('{sys}\taskkill.exe'), '/f /im {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      Sleep(1000);
    end;
  end else
  begin
    // No PID passed (manual install) — just try to kill by name as a safety measure
    Log('No PID passed. Performing name-based cleanup.');
    Exec(ExpandConstant('{sys}\taskkill.exe'), '/f /im {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Sleep(1500);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    Exec(ExpandConstant('{sys}\taskkill.exe'), '/f /im {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;
