echo NOTE: please modify python pkgpath path to your python before build

REM pip install pyinstaller --proxy=http://child-prc.intel.com:913
@REM set pkgpath=C:\\Intel\\DFPython\\virtualenv\\white\\py36\\hlsgui\\Scripts
set pkgpath=C:\\Intel\\DFPython\\virtualenv\\white\\py36\\svdev\\Scripts

set WD=%~dp0

cd %pkgpath%
%pkgpath%\\pyinstaller.exe -F %WD%\\plvl_gui.py --hidden-import prettytable --hidden-import win32gui --hidden-import PyQt5 --hidden-import fabric --hidden-import xmltodict

cd %WD%

@REM del ..\\*.exe
move /Y %pkgpath%\\dist\\*.exe ..