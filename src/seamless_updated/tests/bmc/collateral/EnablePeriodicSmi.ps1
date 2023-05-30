param([String]$computer=0.0.0.0,[String]$user="",[String]$password="", [String]$command="")

#$user = 'Administrator'
#$password = 'Intel123'
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
# Currently set to 72,000 cycles with a 100ms delay between is about 120 minutes
Invoke-Command -ScriptBlock {Rw.exe /command='LOOP{72000, DELAY 100; O16 0xB2 0x0000}'} -Session $s
Remove-PSSession -Session $s
Write-Host "Enable periodic SMI successful"

Write-Host "remote powershell complete"