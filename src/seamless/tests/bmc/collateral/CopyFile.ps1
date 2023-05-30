param([String]$computer=0.0.0.0,[String]$user="",[String]$password="", [String]$version="")
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
Invoke-Command -ScriptBlock {Param($version) C:\Windows\System32\SeamlessUpdateToolbox.ps1 -patchUcode -version $version} -ArgumentList($version) -Session $s
Remove-PSSession -Session $s
<# Invoke-Command -ScriptBlock { Write-Host $version } -ArgumentList($version) -Session $s
Invoke-Command -ScriptBlock {ucscv.exe /uninstall} -Session $s
Invoke-Command -ScriptBlock {Param($version) Copy-Item C:\Windows\System32\Ucode\$version\mcupdate_GenuineIntel.dll C:\Windows\System32\} -ArgumentList($version) -Session $s
Invoke-Command -ScriptBlock {ucscv.exe /uninstall} -Session $s #>

Write-Host "remote powershell complete"
