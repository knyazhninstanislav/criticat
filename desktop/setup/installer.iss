
[Setup]
AppName=CritiCat
AppVersion=1.0.0
DefaultDirName={pf}\CritiCat
DefaultGroupName=CritiCat
UninstallDisplayIcon={app}\CritiCat.exe
OutputDir=installer
OutputBaseFilename=CritiCat_Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\CritiCat.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "testbase"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\CritiCat"; Filename: "{app}\CritiCat.exe"
Name: "{commondesktop}\CritiCat"; Filename: "{app}\CritiCat.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительно:"

[Run]
Filename: "{app}\CritiCat.exe"; Description: "Запустить CritiCat"; Flags: nowait postinstall skipifsilent
