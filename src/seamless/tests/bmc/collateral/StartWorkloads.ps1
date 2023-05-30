param([String]$computer=0.0.0.0,[String]$user="",[String]$password="", [bool]$network_workload=$false)
$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -runWorkload -vmname "MemVM*" -username "wos" -password "intel" -workloadtype "memory"} -Session $s
Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -runWorkload -vmname "DiskVM*" -username "wos" -password "intel" -workloadtype "disk"} -Session $s
Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -runWorkload -vmname "CPUVM*" -username "wos" -password "intel" -workloadtype "cpu"} -Session $s
if ($network_workload) {
    Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -runWorkload -vmname "MemVM*" -username "wos" -password "intel" -workloadtype "network"} -Session $s
}
Write-Host "remote powershell complete"
while(1){
Start-Sleep -s 30000
}