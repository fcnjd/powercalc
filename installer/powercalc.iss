; Powercalc Windows installer.
; AppId is the stable installer identity for future upgrades.

#define MyAppName "Powercalc"
#define MyAppPublisher "Julian Dreykorn"
#define MyAppURL "https://github.com/fcnjd/powercalc"
#define MyAppExeName "Powercalc.exe"

#ifndef AppVersion
#define AppVersion "0.0.0-dev"
#endif

#ifndef SourceDir
#define SourceDir "..\dist\Powercalc"
#endif

#ifndef OutputDir
#define OutputDir "..\dist\release"
#endif

#ifndef OutputBaseFilename
#define OutputBaseFilename "Powercalc-setup"
#endif

[Setup]
AppId={{D8991DBA-AA16-4460-98F7-B06D3E156BDB}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir={#OutputDir}
OutputBaseFilename={#OutputBaseFilename}
SetupIconFile=..\assets\powercalc.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern dynamic

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
