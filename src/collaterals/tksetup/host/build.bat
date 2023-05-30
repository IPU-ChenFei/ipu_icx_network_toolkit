set pkgpath=C:\\Python36\\Scripts
set WD=%~dp0

cd %pkgpath%
%pkgpath%\\pyinstaller.exe -F %WD%\\host_setup.py