; Inno Setup Script for ParrotInk

#define MyAppName "ParrotInk"
#define MyAppVersion "0.2.36"
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
SetupLogging=yes
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
; Senior Architecture: runasoriginaluser ensures the app doesn't inherit Setup's Admin privileges.
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent runasoriginaluser
; Silent install (updates): Force launch automatically because the wizard pages are hidden
Filename: "{app}\{#MyAppExeName}"; Flags: nowait runasoriginaluser; Check: WizardSilent

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
        Log('Wait timed out or failed. Process may still be closing or locked by OS/AV.');
        // Senior Architecture: Attempt one last graceful wait before a hard kill.
        Sleep(2000);

        // Last resort: If still alive, we must kill to avoid "File in use" errors.
        Log('Process still detected. Performing last-resort force kill.');
        Exec(ExpandConstant('{sys}\taskkill.exe'), '/f /im {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
        Sleep(1000);
      end else
      begin
        Log('Process exited gracefully.');
        Sleep(1500); // Normal exit buffer for _MEI cleanup + AV scan latency
      end;
    end else
    begin
      // OpenProcess failed (PID already gone)
      Log('OpenProcess failed. PID is likely already dead. Proceeding.');
      Sleep(1000); // Small buffer for final OS cleanup
    end;
  end else
  begin
    // No PID passed (manual install) — check if any instances are running
    Log('No PID passed. Performing name-based cleanup attempt.');
    // Only graceful kill by name (no /f) for manual installs to allow clean MEI teardown
    Exec(ExpandConstant('{sys}\taskkill.exe'), '/im {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Sleep(2000);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if WizardSilent() then
    begin
      Log('Delaying post-install launch for 3000ms to allow AV scanning before [Run] phase...');
      Sleep(3000);
    end;
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
