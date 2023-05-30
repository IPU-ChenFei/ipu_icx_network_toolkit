@Echo off
if exist C:\DPG_Automation\ (echo yes) else (echo no && mkdir C:\DPG_Automation)
SET dpg_automation_path=c:\DPG_Automation\

:: remove all files from DPG_Automation folder befor copying new files
del /q "%dpg_automation_path%*"
FOR /D %%p IN ("%dpg_automation_path%*.*") DO rmdir "%%p" /s /q

:: copy new files
robocopy /MIR /NFL /NDL /NC /NS /NP ../ %dpg_automation_path% >nul 2>&1

exit 0