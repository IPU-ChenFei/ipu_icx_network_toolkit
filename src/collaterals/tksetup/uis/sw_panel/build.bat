set pkgpath=C:\\Python38\\Scripts
set WD=%~dp0

cd %pkgpath%
%pkgpath%\\pyinstaller.exe -F -i %WD%\\pic\\pwr_ctl.ico %WD%\\sw_panel.py