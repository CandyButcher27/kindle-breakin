$dir = 'C:\Users\sriva\Desktop\Me\kindle\kindle-ai-usage'
$node = (Get-Command node).Source
$user = "$env:USERDOMAIN\$env:USERNAME"
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType S4U

$serverSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew
$serverAction = New-ScheduledTaskAction -Execute $node -Argument '--env-file=.env src/server.mjs' -WorkingDirectory $dir
Register-ScheduledTask -TaskName 'kindletoken-server' -Action $serverAction -Trigger (New-ScheduledTaskTrigger -AtLogOn -User $user) -Principal $principal -Settings $serverSettings -Force | Select-Object TaskName, State

$collectSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -MultipleInstances IgnoreNew -StartWhenAvailable
$collectAction = New-ScheduledTaskAction -Execute $node -Argument '--env-file=.env bin/kindletoken-collect.mjs' -WorkingDirectory $dir
$collectTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours((Get-Date).Hour + 1) -RepetitionInterval (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName 'kindletoken-collect' -Action $collectAction -Trigger $collectTrigger -Principal $principal -Settings $collectSettings -Force | Select-Object TaskName, State
