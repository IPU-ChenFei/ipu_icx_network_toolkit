param([String]$computer=0.0.0.0,[String]$user="",[String]$password="")

#$user = 'Administrator'
#$password = 'Intel123'
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred

#copy start and stop workload
Invoke-Command -ScriptBlock {net use \\10.165.204.30\seamless /user:localhost\seamless seamless} -Session $s
Invoke-Command -ScriptBlock {xcopy  \\10.165.204.30\seamless\To_DEL\SeamlessUpdateToolbox.ps1 C:\Windows\System32} -Session $s
Remove-PSSession -Session $s

<# Invoke-Command -ScriptBlock {xcopy  \\10.165.204.30\seamless\scripts\pve_common\Windows\Target\workloads C:\Workloads /s /i} -Session $s
Invoke-Command -ScriptBlock {mkdir C:\SDK} -Session $s
Invoke-Command -ScriptBlock {xcopy  \\10.165.204.30\seamless\Windows\Demos\PRM\WindowsKits\SDK C:\SDK /s /i} -Session $s
Invoke-Command -ScriptBlock {mkdir C:\WDK} -Session $s
Invoke-Command -ScriptBlock {xcopy  \\10.165.204.30\seamless\Windows\Demos\PRM\WindowsKits\WDK C:\WDK /s /i} -Session $s
Invoke-Command -ScriptBlock { Set-ExecutionPolicy Unrestricted} -Session $s
Invoke-Command -ScriptBlock { Enable-PSRemoting -Force} -Session $s
Invoke-Command -ScriptBlock { NetSh Advfirewall set allprofiles state off} -Session $s
Invoke-Command -ScriptBlock { Set-Item WSMan:\localhost\Client\TrustedHosts -Value '*'} -Session $s
Invoke-Command -ScriptBlock { Restart-Service WinRM} -Session $s #>
Write-Host "remote powershell complete"