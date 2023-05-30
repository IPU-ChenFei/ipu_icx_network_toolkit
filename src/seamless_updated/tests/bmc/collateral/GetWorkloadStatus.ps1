param([String]$computer=0.0.0.0,[String]$user="",[String]$password="")

#$user = 'Administrator'
#$password = 'Intel123'
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred

#Collect platform configuration from windows agent
Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -querySystem -sysconfig "bios" > C:\temp\biosinfo.txt } -Session $s
Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -querySystem -sysconfig "ucode" > C:\temp\ucodeinfo.txt } -Session $s
#Collect error logs
Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -querySystem -sysconfig "eventlogs" > C:\temp\errors.txt } -Session $s
#Collect diskspd logs
Invoke-Command -ScriptBlock { C:\Windows\System32\cmd.exe diskspd.exe .....} -Session $s
Remove-PSSession -Session $s
#collect mlc logs
#collect pbmw logs

Write-Host "remote powershell complete"