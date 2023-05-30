param([String]$computer=0.0.0.0,[String]$user="",[String]$password="", [String]$version="")

#$user = 'Administrator'
#$password = 'Intel123'
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
Invoke-Command -ScriptBlock {C:\Windows\System32\SeamlessUpdateToolbox.ps1 -startflow -flowtype "ksr"} -Session $s
#Invoke-Command -ScriptBlock {vmphuum.exe dk} -Session $s
#Invoke-Command -ScriptBlock {vmphuum.exe g} -Session $s
Invoke-Command -ScriptBlock {Restart-Computer -Force} -Session $s
Remove-PSSession -Session $s
#Start-Sleep -s 40
#Start-Sleep -s 40

Write-Host "remote powershell complete"