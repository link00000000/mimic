#define ApplicationName "Mimic"
#define ApplicationURL "https://github.com/link00000000/mimic"
#define ApplicationExeName "mimic.exe"

; Override application version with /DApplicationVersion=v1.2.3
#ifndef ApplicationVersion
    #define ApplicationVersion "v0.0.0"
#endif

; Override output file name with /DOutputFilename=setup-mimic-win64-debug
#ifndef OutputFilename
    #define OutputFilename "setup-mimic-win64"
#endif

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{4DA90CF3-BA51-422F-A57C-1ABE71E0E802}
AppName={#ApplicationName}
AppVersion={#ApplicationVersion}
AppVerName={#ApplicationName} {#ApplicationVersion}
AppPublisherURL={#ApplicationURL}
AppSupportURL={#ApplicationURL}
AppUpdatesURL={#ApplicationURL}
DefaultDirName={autopf}\{#ApplicationName}
DisableProgramGroupPage=yes
LicenseFile=.\LICENSE
OutputBaseFilename={#OutputFilename}
OutputDir=.\dist
SetupIconFile=.\assets\favicon.ico
PrivilegesRequired=admin
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "Start Mimic when Windows starts"; GroupDescription: "Additional Options"; Flags: checkedonce

[Files]
Source: ".\dist\mimic\{#ApplicationExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: ".\dist\mimic\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: ".\build\OBS-VirtualCam\*"; DestDir: "{app}\OBS-VirtualCam"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\{#ApplicationName}"; Filename: "{app}\{#ApplicationExeName}"
Name: "{autodesktop}\{#ApplicationName}"; Filename: "{app}\{#ApplicationExeName}"; Tasks: desktopicon
Name: "{commonstartup}\{#ApplicationName}"; Filename: "{app}\{#ApplicationExeName}"; Tasks: autostart

[Run]
Filename: "{app}\{#ApplicationExeName}"; Description: "{cm:LaunchProgram,{#StringChange(ApplicationName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
Filename: "{sys}\Regsvr32.exe"; Parameters: "/n /i:1 /s OBS-VirtualCam\bin\32bit\obs-virtualsource.dll"; WorkingDir: "{app}"; StatusMsg: "Registering OBS-VirtualCam 32bit"; Flags: runhidden
Filename: "{sys}\Regsvr32.exe"; Parameters: "/n /i:1 /s OBS-VirtualCam\bin\64bit\obs-virtualsource.dll"; WorkingDir: "{app}"; StatusMsg: "Registering OBS-VirtualCam 64bit"; Flags: runhidden

[UninstallRun]
Filename: "{sys}\Regsvr32.exe"; Parameters: "/u /s OBS-VirtualCam\bin\32bit\obs-virtualsource.dll"; WorkingDir: "{app}"; StatusMsg: "Unregistering OBS-VirtualCam 32bit"; Flags: runhidden
Filename: "{sys}\Regsvr32.exe"; Parameters: "/u /s OBS-VirtualCam\bin\64bit\obs-virtualsource.dll"; WorkingDir: "{app}"; StatusMsg: "Unregistering OBS-VirtualCam 64bit"; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}/mimic"

; NOTE Setting registry entry cannot be done with [Registry] because it will be
; overwritten when OBS-VirtualCam DLLs are installed
[Code]
{ Set correct camera name in registry }
procedure SetCameraNameRegistryEntry();
begin
    Log('Writing registry entry for camera name')
    RegWriteStringValue(
        HKEY_CLASSES_ROOT, 'WOW6432Node\CLSID\{860BB310-5D01-11d0-BD3B-00A0C911CE86}\Instance\{27B05C2D-93DC-474A-A5DA-9BBA34CB2A9C}', 'FriendlyName', 'Mimic');
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
    Log('CurStepChanged(' + IntToStr(Ord(CurStep)) + ') called')
    if CurStep = ssPostInstall then
        SetCameraNameRegistryEntry();
    begin
    end;
end;
