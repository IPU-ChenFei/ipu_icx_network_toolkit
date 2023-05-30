param([String]$computer=0.0.0.0,[String]$user="",[String]$password="")

#$user = 'Administrator'
#$password = 'Intel123'
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
Invoke-Command -ScriptBlock { cd "C:\test\"; .\App.exe } -Session $s
#Invoke-Command -ScriptBlock {C:\test\App.exe} -Session $s
Remove-PSSession -Session $s
Write-Host "remote powershell complete `n"
