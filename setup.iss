#define ApplicationName "Mimic"
#define ApplicationURL "https://github.com/link00000000/mimic"
#define ApplicationExeName "mimic.exe"

; Override application version with /DApplicationVersion=1.2.3
#ifndef ApplicationVersion
    #define ApplicationVersion "0.0.0"
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
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: ".\dist\mimic\{#ApplicationExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: ".\dist\mimic\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{autoprograms}\{#ApplicationName}"; Filename: "{app}\{#ApplicationExeName}"
Name: "{autodesktop}\{#ApplicationName}"; Filename: "{app}\{#ApplicationExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#ApplicationExeName}"; Description: "{cm:LaunchProgram,{#StringChange(ApplicationName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

