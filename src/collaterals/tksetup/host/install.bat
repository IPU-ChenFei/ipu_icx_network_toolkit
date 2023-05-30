:: Date 2021/05/31
@echo off
set WD=%~dp0

:: 1.Set proxy
echo --------------------------------------
echo ^| Provide below proxy for reference  ^|
echo --------------------------------------
echo ^|  China: child-prc.intel.com:913    ^|
echo ^|  India: proxy01.iind.intel.com:911 ^|
echo ^|  American: proxy-us.intel.com:911  ^|
echo ^|  Common: proxy-chain.intel.com:911 ^|
echo --------------------------------------

if "%1%" == "" (
echo No need to set proxy
) else (
if "%2%" == "" (
set http_proxy=%1%
set https_proxy=%1%
echo Set http_proxy=%http_proxy% done!
echo Set https_proxy=%https_proxy% done!
) else (
set http_proxy=%1%
set https_proxy=%2%
echo Set http_proxy=%http_proxy% done!
echo Set https_proxy=%https_proxy% done!
)
)

:: 1.Install VC++2015U3
set vcpp_file="C:\Program Files (x86)\Microsoft Visual C++ Build Tools\vcbuildtools.bat"
if exist %vcpp_file% echo "vc++ 2015 buildtools already installed..."
if not exist %vcpp_file% echo "install vc++ 2015 buildtools..."
if not exist %vcpp_file% %WD%\tools\vcpp2015u3\VisualCppBuildTools_Full.exe /Passive

:: 2.Install python3 interpreter
echo.
set python36="C:\Python36\python.exe"
if exist %python36% echo "python36 already installed..."
if not exist %python36% echo "install python36..."
if not exist %python36% set reboot_y="yes"
if not exist %python36% %WD%\tools\python-3.6.8-amd64.exe /passive InstallAllUsers=1 PrependPath=1 TargetDir=C:\Python36
::if %reboot_y%=="yes" shutdown /r /t 3

:: 3.check internet network connection
echo.
echo "check internet connection status..."
nslookup intel.com
if %errorlevel% == 0 (
  echo "check internet connection PASS..."
) else (
  echo "check internet connection FAILED..."
  echo "Pls check your internet connection MANUALLY..."
  exit 1
)

:: 4.Update pip
echo.
set python36_dir="C:\Python36"

echo update pip software...
%python36_dir%\python -m pip install --upgrade pip

:: 5.Install dtaf-rore source code and requirements
%python36_dir%\python -m pip install -r requirements.txt
%python36_dir%\python -m pip install xmltodict wcwidth pathlib2 artifactory anybadge

:: 6.Install automation framework requirements(pyqt5,pywin32,prettytable)
echo.
echo "install automation framework requirements pyqt5,pywin32,prettytable..."
%python36_dir%\python -m pip install pyqt5 pywin32 prettytable

:: 7.copy ipmitoolkit to C:
echo "copy ipmitoolkit folder to C disk"
xcopy /E /Y /I %WD%\tools\ipmitoolkit C:\ipmitoolkit

:: 8.install rsc2 driver
set sdk="C:\Program Files (x86)\RSC 2 Software\uninst.exe"
if exist %sdk% echo "RSC_2_Installer_2.0.exe already installed..."
if not exist %sdk% echo "install RSC_2_Installer_2.0.exe..."
if not exist %sdk% %WD%\tools\RSC_2_Installer_2.0.exe /S

:: 9.install banino tool
echo "copy banino tool folder to C disk"
xcopy /E /Y /I %WD%\tools\banino C:\banino