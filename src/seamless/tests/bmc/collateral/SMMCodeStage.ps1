param([String]$computer=0.0.0.0,[String]$user="",[String]$password="", [String]$capsule="")
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
Invoke-Command -ScriptBlock {Param($capsule) C:\Windows\System32\SeamlessUpdateToolbox.ps1 -sruFlow codeStage -codeInjectionCapsule $capsule} -ArgumentList($capsule) -Session $s
Remove-PSSession -Session $s

Write-Host "remote powershell complete"
