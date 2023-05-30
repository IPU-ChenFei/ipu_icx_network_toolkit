param([String]$computer=0.0.0.0,[String]$user="",[String]$password="", [String]$version="", [String]$time="")

$pass = ConvertTo-SecureString -String $password -AsPlainText -Force
$cred = New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList $user, $pass
$s = New-PSSession -ComputerName $computer -credential $cred
Write-Host $time
$date = [datetime]::parseexact($time, 'MM/dd/yyyy HH:mm:ss', $null)
#Invoke-Command -ScriptBlock { C:\Windows\System32\SeamlessUpdateToolbox.ps1 -querySystem -sysconfig "eventlogs"} -Session $s
#Invoke-Command -ScriptBlock { Param{$time} Get-EventLog -LogName System -Newest 1000 -After (Get-Date).AddDays(-1) | Where-Object {$_.EntryType -eq "Error"} | Format-Table -auto -wrap; Get-EventLog -LogName Application -Newest 1000 -After (Get-Date).AddDays(-1)| Where-Object {$_.EntryType -eq "error"} | Format-Table -auto -wrap} -Session $s
#Invoke-Command -ScriptBlock {Param($time) Get-EventLog -LogName System -Newest 1000 -After $time | Where-Object {$_.EntryType -eq "Error"} | Format-Table -auto -wrap; Get-EventLog -LogName Application -Newest 1000 -After $time| Where-Object {$_.EntryType -eq "error"} | Format-Table -auto -wrap} -Session $s -ArgumentList($time)
#?{$_.TimeGenerated -match "04:[0-2][0-9]:[0-5][0-9]"}
#$date = [datetime]$time
#$datenow = $d
Write-Host $date.gettype()
Write-Host Get-Date
Invoke-Command -ScriptBlock {Param($date) Get-EventLog -LogName System -Newest 1000 -After $date| Where-Object {$_.EntryType -eq "Error"} | Format-Table -auto -wrap; Get-EventLog -LogName Application -Newest 1000 -After $date | Where-Object {$_.EntryType -eq "error"} | Format-Table -auto -wrap} -Session $s -ArgumentList ($date)
Remove-PSSession -Session $s

Write-Host "remote powershell complete"
