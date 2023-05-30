param([String]$computer=0.0.0.0,[String]$user="",[String]$password="", [String]$capsule="")
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
Invoke-Command -ScriptBlock {Param($capsule) C:\Windows\System32\SeamlessUpdateToolbox.ps1 -sruFlow codeInject -codeInjectionCapsule C:\Windows\System32\capsules\$capsule} -ArgumentList($capsule) -Session $s
Remove-PSSession -Session $s
<# If ($command -eq '-a'){
	Invoke-Command -ScriptBlock {Param($command) C:\SeamlessUpdate_SMMRT_0P9\bin\exe\SruApp.exe $command} -ArgumentList($command) -Session $s
}
else{
	Invoke-Command -ScriptBlock {Param($command, $capsule) C:\SeamlessUpdate_SMMRT_0P9\bin\exe\SruApp.exe $command C:\SeamlessUpdate_SMMRT_0P9\bin\capsules\$capsule} -ArgumentList($command, $capsule) -Session $s
} #>
Write-Host "remote powershell complete"
