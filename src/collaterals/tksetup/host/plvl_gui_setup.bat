:: Date 2022/06/10
@echo off
set WD=%~dp0

if "%1%" == "" (
set pyenvpath="C:\Python36"
) else (
set pyenvpath=%1%
)
echo Set python to = %pyenvpath%\python

:: 1.Update pip
echo.
echo update pip software...
%pyenvpath%\python -m pip install --upgrade pip

:: 2.Install dtaf-core lib and requirements
@REM xcopy /E /Y %WD%\frameworks.automation.dtaf.core-production.zip C:\Python36\Lib\site-packages
%pyenvpath%\python -m pip install frameworks.automation.dtaf.core-production.zip
%pyenvpath%\python -m pip install xmltodict wcwidth pathlib2 artifactory anybadge

:: 3.Install automation framework requirements(pyqt5,pywin32,prettytable)
echo.
echo "install automation framework requirements pyqt5,pywin32,prettytable..."
%pyenvpath%\python -m pip install pyqt5 pywin32 prettytable fabric openpyxl wxpython

