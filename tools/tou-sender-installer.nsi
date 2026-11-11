Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"
!include "x64.nsh"
!include "WinVer.nsh"
!ifndef APPDIR
!error "APPDIR required"
!endif
!ifndef OUTFILE
!error "OUTFILE required"
!endif
!ifndef UNINSTALL_MANIFEST
!error "UNINSTALL_MANIFEST required"
!endif
!include "${UNINSTALL_MANIFEST}"
Name "GRAND DIGITAL TOU Sender"
OutFile "${OUTFILE}"
InstallDir "$LOCALAPPDATA\Programs\GrandDigital\TOUSender"
InstallDirRegKey HKCU "Software\GrandDigital\TOUSender" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
ShowInstDetails show
ShowUninstDetails show
VIProductVersion "1.2.0.0"
VIAddVersionKey "ProductName" "GRAND DIGITAL TOU Sender"
VIAddVersionKey "FileDescription" "TOU Sender Setup for Windows 10/11 x64"
VIAddVersionKey "FileVersion" "1.2.0"
VIAddVersionKey "LegalCopyright" "Grand Digital"
Var TestMode
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "GRAND DIGITAL TOU Sender"
!define MUI_WELCOMEPAGE_TEXT "โปรแกรมส่งไฟล์ TOU สำหรับ Windows 10/11 แบบ 64-bit$\r$\n$\r$\nไม่ต้องติดตั้ง Python แยก$\r$\nติดตั้งเสร็จแล้วเลือกไฟล์ตั้งค่าการเชื่อมต่อครั้งแรก และกดเริ่มส่งข้อมูล$\r$\n$\r$\nไม่มีการแก้ไขไฟล์ TOU ต้นฉบับหรือระบบ MySQL"
!define MUI_FINISHPAGE_RUN "$INSTDIR\TOUSender.exe"
!define MUI_FINISHPAGE_RUN_TEXT "เปิด TOU Sender"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "Thai"
!insertmacro MUI_LANGUAGE "English"

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "โปรแกรมนี้รองรับ Windows 64-bit เท่านั้น" /SD IDOK
    Abort
  ${EndIf}
  ${IfNot} ${AtLeastWin10}
    MessageBox MB_ICONSTOP "โปรแกรมนี้รองรับ Windows 10 หรือใหม่กว่า" /SD IDOK
    Abort
  ${EndIf}
  StrCpy $TestMode "0"
  ${GetParameters} $R0
  ClearErrors
  ${GetOptions} $R0 "/TEST" $R1
  ${IfNot} ${Errors}
    StrCpy $TestMode "1"
  ${EndIf}
FunctionEnd

Section "ติดตั้ง"
  IfFileExists "$INSTDIR\TOUSender.exe" check_install_marker
  IfFileExists "$INSTDIR\_internal\*.*" check_install_marker install_files
  check_install_marker:
  ClearErrors
  FileOpen $0 "$INSTDIR\tou-sender.installmarker" r
  IfErrors invalid_install_dir
  FileRead $0 $1
  FileClose $0
  StrCmp $1 "GrandDigital-TOU-Sender-1" known_installation
  invalid_install_dir:
  MessageBox MB_ICONSTOP "โฟลเดอร์นี้มีไฟล์โปรแกรมอื่น กรุณาเลือกโฟลเดอร์ใหม่" /SD IDOK
  Abort
  known_installation:
  ${If} $TestMode == "0"
    ExecWait '"$INSTDIR\TOUSender.exe" --shutdown' $0
    ${If} $0 != 0
      MessageBox MB_ICONSTOP "กรุณาหยุด TOU Sender ก่อนอัปเดตโปรแกรม" /SD IDOK
      Abort
    ${EndIf}
  ${EndIf}
  install_files:
  SetOutPath "$INSTDIR"
  File /r "${APPDIR}\*"
  FileOpen $0 "$INSTDIR\tou-sender.installmarker" w
  FileWrite $0 "GrandDigital-TOU-Sender-1"
  FileClose $0
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  ${If} $TestMode == "0"
    SetShellVarContext current
    CreateDirectory "$SMPROGRAMS\Grand Digital"
    CreateShortCut "$SMPROGRAMS\Grand Digital\TOU Sender.lnk" "$INSTDIR\TOUSender.exe"
    CreateShortCut "$DESKTOP\TOU Sender.lnk" "$INSTDIR\TOUSender.exe"
    WriteRegStr HKCU "Software\GrandDigital\TOUSender" "InstallDir" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GrandDigitalTOUSender" "DisplayName" "GRAND DIGITAL TOU Sender"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GrandDigitalTOUSender" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GrandDigitalTOUSender" "DisplayVersion" "1.2.0"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GrandDigitalTOUSender" "Publisher" "Grand Digital"
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GrandDigitalTOUSender" "NoModify" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GrandDigitalTOUSender" "NoRepair" 1
  ${EndIf}
SectionEnd

Function un.onInit
  StrCpy $TestMode "0"
  ${GetParameters} $R0
  ClearErrors
  ${GetOptions} $R0 "/TEST" $R1
  ${IfNot} ${Errors}
    StrCpy $TestMode "1"
  ${EndIf}
  ClearErrors
  FileOpen $0 "$INSTDIR\tou-sender.installmarker" r
  IfErrors unsafe
  FileRead $0 $1
  FileClose $0
  StrCmp $1 "GrandDigital-TOU-Sender-1" verified
  unsafe:
  MessageBox MB_ICONSTOP "ไม่พบข้อมูลการติดตั้งที่ถูกต้อง จึงไม่ลบไฟล์" /SD IDOK
  Abort
  verified:
FunctionEnd

Section "Uninstall"
  ${If} $TestMode == "0"
    ExecWait '"$INSTDIR\TOUSender.exe" --shutdown' $0
    ${If} $0 != 0
      MessageBox MB_ICONSTOP "กรุณาหยุด TOU Sender ก่อนถอนการติดตั้ง" /SD IDOK
      Abort
    ${EndIf}
  ${EndIf}
  !insertmacro RemoveInstalledFiles
  Delete "$INSTDIR\tou-sender.installmarker"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  ${If} $TestMode == "0"
    SetShellVarContext current
    Delete "$SMPROGRAMS\Grand Digital\TOU Sender.lnk"
    RMDir "$SMPROGRAMS\Grand Digital"
    Delete "$DESKTOP\TOU Sender.lnk"
    DeleteRegKey HKCU "Software\GrandDigital\TOUSender"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GrandDigitalTOUSender"
  ${EndIf}
SectionEnd
