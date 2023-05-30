param([String]$computer=0.0.0.0,[String]$user="",[String]$password="", [bool]$network_workload=$false)

#$user = 'Administrator'
#$password = 'Intel123'
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
<# Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -startVM -vmname "CPUVM0"} -Session $s
Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -startVM -vmname "DiskVM0"} -Session $s
Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -startVM -vmname "MemVM0"} -Session $s
Start-Sleep -s 5
Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -startVM -vmname "CPUVM0"} -Session $s
Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -startVM -vmname "DiskVM0"} -Session $s
Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -startVM -vmname "MemVM0"} -Session $s
Start-Sleep -s 10 #>
Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -stopWorkload -vmname "CPUVM0" -username "wos" -password "intel" -workloadtype "cpu"} -Session $s
Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -stopWorkload -vmname "MemVM0" -username "wos" -password "intel" -workloadtype "memory"} -Session $s
Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -stopWorkload -vmname "DiskVM0" -username "wos" -password "intel" -workloadtype "disk"} -Session $s
if ($network_workload) {
    Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -stopWorkload -vmname "MemVM0" -username "wos" -password "intel" -workloadtype "network"} -Session $s
}
Remove-PSSession -Session $s

#Invoke-Command -ScriptBlock { C:\workloads\start_workloads.ps1 } -Session $s
#Invoke-Command -ScriptBlock { C:\workloads\stop_workloads.ps1 } -Session $s

Write-Host "remote powershell complete"