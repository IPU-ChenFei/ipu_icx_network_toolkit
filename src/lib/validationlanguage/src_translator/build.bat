echo NOTE: please modify python pkgpath path to your python before build

REM pip install pyinstaller --proxy=http://child-prc.intel.com:913
@REM set pkgpath=C:\Intel\DFPython\virtualenv\white\py36\hls\Scripts
set pkgpath=C:\\Python310\\Scripts


set WD=%~dp0

cd %pkgpath%
echo %pkgpath%\\pyinstaller.exe -F %WD%\\translator_l2py.py
echo %pkgpath%\\pyinstaller.exe -F %WD%\\translator_h2l.py
echo %pkgpath%\\pyinstaller.exe -F %WD%\\translator_tcd.py
%pkgpath%\\pyinstaller.exe -F %WD%\\vl_translator.py --hidden-import xmltodict

cd %WD%

move /Y %pkgpath%\\dist\\*.exe ..