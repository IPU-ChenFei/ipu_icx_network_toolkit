param([String]$computer=0.0.0.0,[String]$user="",[String]$password="", [String]$command="")
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
Invoke-Command -ScriptBlock {Get-Content -Path C:\SSTS.log} -Session $s
Remove-PSSession -Session $s
#Invoke-Command -ScriptBlock {C:\SeamlessUpdate_SMMRT_0P9\bin\exe\SruApp.exe -q} -Session $s

Write-Host "remote powershell complete"
