param([String]$computer=0.0.0.0,[String]$user="",[String]$password="")
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
Invoke-Command -ScriptBlock {REG QUERY "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\ACPI\Parameters" /v PrmSupportGranted} -Session $s
Remove-PSSession -Session $s

Write-Host "remote powershell complete"
