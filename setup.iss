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
    Log('Writing registry entry for camera name');
    RegWriteStringValue(
        HKEY_CLASSES_ROOT, 'WOW6432Node\CLSID\{860BB310-5D01-11d0-BD3B-00A0C911CE86}\Instance\{27B05C2D-93DC-474A-A5DA-9BBA34CB2A9C}', 'FriendlyName', 'Mimic');
end;

{
    Add rule to Windows Firewall to allow inbound traffic
    @NOTE Adapted from https://web.archive.org/web/20170313090648/http://www.vincenzo.net/isxkb/index.php?title=Adding_a_rule_to_the_Windows_firewall
    @NOTE Adapted from https://github.com/HeliumProject/InnoSetup/blob/master/Examples/CodeAutomation.iss
}
{ These are winapi enum values from https://github.com/Alexpux/mingw-w64/blob/d0d7f784833bbb0b2d279310ddc6afb52fe47a46/mingw-w64-headers/include/icftypes.hh }
const
    NET_FW_IP_VERSION_ANY = 2;
    NET_FW_SCOPE_ALL = 0;

procedure AddWindowsFilewallRule();
var
    Firewall, Application: Variant;
begin
    Log('Adding rule to Windows Firewall');

    { Create Windows Firewall Automation object }
    try
        Firewall := CreateOleObject('HNetCfg.FwMgr');
    except
        RaiseException('Could not access Windows Firewall. Make sure it is installed first.');
    end;

    { Add Windows Firewall authorization rule }
    Application := CreateOleObject('HNetCfg.FwAuthorizedApplication')
    Application.Name := 'Mimic'
    Application.IPVersion := NET_FW_IP_VERSION_ANY;
    Application.ProcessImageFileName := ExpandConstant('{app}/{#ApplicationExeName}');
    Application.Scope := NET_FW_SCOPE_ALL;
    Application.Enabled := True;

    Firewall.LocalPolicy.CurrentProfile.AuthorizedApplications.Add(Application);

    Log('Windows Firewall rule added');
end;

{
    Remove all Windows Firewall rules set during installation
    @NOTE See https://docs.microsoft.com/en-us/windows/win32/api/netfw/nf-netfw-inetfwauthorizedapplications-remove
    @NOTE See https://github.com/Alexpux/mingw-w64/blob/d0d7f784833bbb0b2d279310ddc6afb52fe47a46/mingw-w64-headers/include/icftypes.hh
    @NOTE See https://github.com/getlantern/winfirewall/blob/caf28a30bcd27902196e00520956ce98a3d3f888/netfw.h
}
procedure RemoveWindowsFirewallRule();
var
    Firewall: Variant;
begin
    Log('Removing rule from Windows Firewall')

    { Create Windows Firewall Automation object }
    try
        Firewall := CreateOleObject('HNetCfg.FwMgr');
    except
        RaiseException('Could not access Windows Firewall. Firewall rule may need to be removed manually');
    end;

    MsgBox(ExpandConstant('{app}\{#ApplicationExeName}'), mbInformation, mb_Ok)
    Firewall.LocalPolicy.CurrentProfile.AuthorizedApplications.Remove(ExpandConstant('{app}\{#ApplicationExeName}'));

    Log('Windows Firewall rule removed')
end;

{ Automatically run every time a step in the installation changes }
procedure CurStepChanged(CurStep: TSetupStep);
begin
    Log('CurStepChanged(' + IntToStr(Ord(CurStep)) + ') called');
    if CurStep = ssPostInstall then
        SetCameraNameRegistryEntry();
    if CurStep = ssDone then
        AddWindowsFilewallRule();
end;

{ Automatically run every time a step in the uninstalltion changes }
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
    Log('CurUninstallSetpChanged(' + IntToStr(Ord(CurUninstallStep)) + ') called');
    if CurUninstallStep = usPostUninstall then
        RemoveWindowsFirewallRule();
end;
