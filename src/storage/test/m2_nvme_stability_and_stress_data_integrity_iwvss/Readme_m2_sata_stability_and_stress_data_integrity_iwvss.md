For TC : ["16013617630", "M.2 NVME-Stability and Stress- Data integrity - IWVSS(windows)"]

1. M.2 NVMe SSD should be connected in SUT.
2. SATA SSD
Update iwvss information in content_config.xml as below,

Example:
<ilwss>
    <!-- iwvss exe file name -->
    <iwvss_exe_file_name>iwVSS_2.9.2.exe</iwvss_exe_file_name>
    <!-- iwvss licence key file name -->
    <iwvss_licence_key>VSS_Site_12-01-2022_license.key</iwvss_licence_key>
    <!-- iwvss tool run time in minutes -->
    <iwvss_run_time>5</iwvss_run_time>
</ilwss>

<nvme_m2_drive_name>Samsung SSD 980 1TB</nvme_m2_drive_name>        
