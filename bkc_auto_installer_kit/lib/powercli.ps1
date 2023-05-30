echo Y;Set-PSRepository -Name PSGallery -InstallationPolicy Trusted  
Install-Module -Name VMware.PowerCLI 
$newDir = "C:\Windows\assembly\GAC_64\log4net\1.2.10.0__692fbea5521e1304" 
New-Item $newDir -ItemType directory -Force 
$file = gci "C:\Program Files\WindowsPowerShell\Modules\VMware.VimAutomation.Sdk" | select -last 1 | gci -Recurse -Filter "log4net.dll" | select -first 1 
Copy-Item $file.FullName $newDir 
Get-ChildItem $newDir 
echo "Installation of PowerCli Done"