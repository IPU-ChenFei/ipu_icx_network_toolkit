param([String]$computer=0.0.0.0,[String]$user="",[String]$password="")
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -startVM -vmname "CPUVM*"} -Session $s
Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -startVM -vmname "DiskVM*"} -Session $s
Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -startVM -vmname "MemVM*"} -Session $s
Remove-PSSession -Session $s
Write-Host "remote powershell complete"
