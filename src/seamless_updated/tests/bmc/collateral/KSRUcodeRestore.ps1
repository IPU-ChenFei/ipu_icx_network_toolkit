param([String]$computer=0.0.0.0,[String]$user="",[String]$password="", [String]$version="")

#$user = 'Administrator'
#$password = 'Intel123'
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
#Invoke-Command -ScriptBlock {C:\Windows\System32\SeamlessUpdateToolbox.ps1 -startflow -flowtype "vmrestore"} -Session $s
Invoke-Command -ScriptBlock {vmphuum.exe r} -Session $s
Remove-PSSession -Session $s
Start-Sleep -s 30
#Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -querySystem -sysconfig "ucode"} -Session $s

Write-Host "remote powershell complete"