param([String]$computer=0.0.0.0,[String]$user="",[String]$password="", [String]$version="")
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
Invoke-Command -ScriptBlock {Param($version) C:\Windows\System32\SeamlessUpdateToolbox.ps1 -dcpmmFlow stageFW -FwRevision $version -NFITHandles all} -Session $s -ArgumentList($version)
Remove-PSSession -Session $s

Write-Host "remote powershell complete"
