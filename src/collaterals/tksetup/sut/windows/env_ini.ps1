echo @off

$rootpath='C:\BKCPkg\tools'

# 3.modify powreshell execution policy as bypass
sleep 1
echo "modify powreshell execution policy as [Bypass]..."
Set-ExecutionPolicy -ExecutionPolicy Bypass

# 4.install xmlcli tool
sleep 1
echo "install xmlcli tool..."
$xmlcli_zip="$rootpath\7.0_xmlcli_windows_linux_esxi_Python2&3_ipclean.zip"
Expand-Archive -Force -Path $xmlcli_zip -DestinationPath $rootpath
Copy-Item -Path "$rootpath\xmlcli" -Destination 'C:\BKCPkg' -Recurse -Force
rm -r "$rootpath\xmlcli"

# 5.disable firewall
sleep 1
echo "disable firewall..."
netsh advfirewall set allprofiles state off

# 6.copy devchk dir to C:\BKCPkg
sleep 1
echo 'copy devch dir to  C:\BKCPkg...'
$devchk_zip="$rootpath\devchk.zip"
Expand-Archive -Force -Path $xmlcli_zip -DestinationPath $rootpath
Copy-Item -Path "$rootpath\devchk" -Destination 'C:\BKCPkg' -Recurse -Force

# 7.copy devchk python packages to py36 sit-packages
sleep 1
echo 'install python site-packages offline by copying...'
$devchk_win_pkg="$rootpath\devchk_win_packages.zip"
Expand-Archive -Force -Path $devchk_win_pkg -DestinationPath $rootpath
Copy-Item -Path "$rootpath\devchk_win_packages\*" -Destination 'C:\Python36\Lib\site-packages' -Recurse -Force

# 8. suppress progress bar in powershell cmds
$pscfg = $PROFILE.AllUsersAllHosts
if ($(Test-Path $pscfg) -ne $true) {
New-Item -Path $pscfg -ItemType "file" -Force
}

$is_append = Get-Content $pscfg|findstr "SilentlyContinue"
if (! $is_append) {
$string = '$ProgressPreference = "SilentlyContinue"'
$string | Out-File -FilePath $pscfg -Append
}