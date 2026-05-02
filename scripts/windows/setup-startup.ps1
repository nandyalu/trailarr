# Register Trailarr as a Task Scheduler startup task for the current user.

$InstallDir = "C:\Program Files\Trailarr"
$Exe        = "$InstallDir\backend\.venv\Scripts\trailarr.exe"
$Script     = "$InstallDir\scripts\start\start.py"

$action = New-ScheduledTaskAction -Execute "`"$Exe`"" -Argument "`"$Script`""

$trigger = New-ScheduledTaskTrigger -AtLogon -User $env:USERNAME

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit  0 `
    -RestartCount        3 `
    -RestartInterval     (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable

$principal = New-ScheduledTaskPrincipal `
    -UserId    $env:USERNAME `
    -LogonType S4U `
    -RunLevel  Limited

Register-ScheduledTask `
    -TaskName   "Trailarr" `
    -Description "Trailarr - Trailer downloader for Radarr and Sonarr" `
    -Action     $action `
    -Trigger    $trigger `
    -Settings   $settings `
    -Principal  $principal `
    -Force | Out-Null

Write-Host "Trailarr registered as a startup task for $env:USERNAME."
Write-Host ""
Write-Host "To start it now (without rebooting):"
Write-Host "  Start-ScheduledTask -TaskName 'Trailarr'"
Write-Host ""
Write-Host "To check status:"
Write-Host "  (Get-ScheduledTask -TaskName 'Trailarr').State"
