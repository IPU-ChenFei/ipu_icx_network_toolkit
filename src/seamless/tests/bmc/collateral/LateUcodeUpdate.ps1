param([String]$computer=0.0.0.0,[String]$user="",[String]$password="", [String]$version="")
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
Invoke-Command -ScriptBlock {C:\Windows\System32\SeamlessUpdateToolbox.ps1 -startflow -flowtype "latebinding"} -Session $s
Remove-PSSession -Session $s
#Invoke-Command -ScriptBlock {ucsvc.exe} -Session $s

Write-Host "remote powershell complete"
