::date:2021-05-24

@echo off
set toolpath=C:\\BKCPkg\\tools
set sut_linux_tools=sut_windows_tools.txt
set sut_tools_url=https://ubit-artifactory-sh.intel.com/artifactory/validationtools-sh-local/env/sut/windows
SETLOCAL DISABLEDELAYEDEXPANSION
timeout 1

:: 1. download tools
powershell.exe (New-Object System.Net.WebClient).DownloadFile('https://ubit-artifactory-sh.intel.com/artifactory/validationtools-sh-local/env/sut/windows/sut_windows_tools.txt', 'C:\BKCPkg\tools\sut_windows_tools.txt')

setlocal EnableDelayedExpansion
for /f "delims=" %%i in (%toolpath%\\%sut_linux_tools%) do (
  set src='%sut_tools_url%/%%i'
  set dst='%toolpath%\\%%i'
  powershell.exe "(New-Object System.Net.WebClient).DownloadFile(!src!,!dst!)"
)

:: 2.install python3 interpreter
set python36="C:\Python36\python.exe"
if exist %python36% echo "python36 already installed..."
if not exist %python36% echo "install python36..."
if not exist %python36% set reboot_y="yes"
if not exist %python36% %toolpath%\\python-3.6.8-amd64.exe /passive InstallAllUsers=1 PrependPath=1 TargetDir=C:\Python36
xcopy %toolpath%\\set_toolkit_src_root.py C:\\Python36\\Lib\\site-packages /Y
::if %reboot_y%=="yes" shutdown /r /t 3

:: 3.modify powreshell execution policy as bypass
:: 4.install xmlcli tool
:: 5.disable firewal
:: 6.copy devchk dir to C:\BKCPkg
:: 7.copy devchk python packages to py36 sit-packages
powershell.exe -ExecutionPolicy Bypass -File "env_ini.ps1"

:: 8.stop powershell server service
timeout 1
echo "stop powershell service..."
set powershellpath="C:\Program Files\nsoftware\PowerShell Server 2016\PowerShellServer.exe"
if exist %powershellpath% (%powershellpath% /servicestop && %powershellpath% /stop)

:: 9.install openssh and start servicer
timeout 1
echo.
echo "install openssh..."
set openssh_zip=%toolpath%\\OpenSSH.zip
powershell.exe Expand-Archive -Force -Path %openssh_zip% -DestinationPath C:\\
::xcopy /Y %toolpath%\\OpenSSH  "C:\OpenSSH\"
powershell.exe -ExecutionPolicy Bypass -File "C:\\OpenSSH\\install-sshd.ps1"

timeout 1
echo.
echo "install openssh service..."
sc config sshd start=auto

timeout 1
echo.
echo "start openssh service..."
net start sshd

:: 10. unzip ipmitoolkit_win.zip
set ipmitool_zip=%toolpath%\\ipmitoolkit_win.zip
powershell.exe Expand-Archive -Force -Path %ipmitool_zip% -DestinationPath %toolpath%

:: 10.install CCBSDK_Internal.exe
set sdk="C:\Program Files\Intel Corporation\Intel(R)CCBSDK\SetupFile\GenSpecCCBSDK.bat"
if exist %sdk% echo "CCBSDK_Internal.exe already installed..."
if not exist %sdk% echo "install CCBSDK_Internal.exe..."
if not exist %sdk% %toolpath%\\IntelCCBSDK_Internal.exe /s

:: 11. print promption info
echo ---------------------------------------------------------------------------
echo ^|                               PROMPTION                                 ^|
echo ---------------------------------------------------------------------------
echo ^| Don't forget to check your ssh communication network port, if use dhcp, ^|
echo ^| make sure it works fine; if use back-to-back connection to sut, make    ^|
echo ^| sure the internal static ip  address is assigned, such as 192.168.1.x   ^|
echo ^| And also, you need to configure this ip address to host config file:    ^|
echo ^| sut.ini/[sutos] section.                                                ^|
echo ---------------------------------------------------------------------------
