@Echo off

SET dpg_automation_path=C:\Testing\FrameworkBuilds\DTAF\

:: remove all files from DPG_Automation folder befor copying new files
del /q "%dpg_automation_path%*"
FOR /D %%p IN ("%dpg_automation_path%*.*") DO rmdir "%%p" /s /q


exit 0