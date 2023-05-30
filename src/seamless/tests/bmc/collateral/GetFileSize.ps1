param([String]$computer=0.0.0.0,[String]$user="",[String]$password="", [String]$filePath="")
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
Invoke-Command -ScriptBlock {Param($filePath) [int][Math]::Ceiling((Get-Item $filePath).length / 1024)} -ArgumentList ($filePath) -Session $s
Remove-PSSession -Session $s

Write-Host "remote powershell complete"
