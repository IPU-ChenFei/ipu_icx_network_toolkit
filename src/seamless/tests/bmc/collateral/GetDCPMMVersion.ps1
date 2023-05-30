param([String]$computer=0.0.0.0,[String]$user="",[String]$password="", [String]$command="")
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
Invoke-Command -ScriptBlock {Param($command)C:\Windows\System32\SeamlessUpdateToolbox.ps1 -dcpmmFlow FwVersion -NFITHandles all} -Session $s -ArgumentList ($command)
Remove-PSSession -Session $s
#Invoke-Command -ScriptBlock {"get dcpmm version"} -Session $s

Write-Host "remote powershell complete"
