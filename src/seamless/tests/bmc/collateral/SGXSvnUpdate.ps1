param([String]$computer=0.0.0.0,[String]$user="",[String]$password="", [String]$cmd="")
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
Invoke-Command -ScriptBlock { Param($cmd) SeamlessUpdateToolbox.ps1 -startFlow -flowtype "sgx_svnupdate"} -ArgumentList($cmd) -Session $s
Remove-PSSession -Session $s
Write-Host "remote powershell complete `n"

