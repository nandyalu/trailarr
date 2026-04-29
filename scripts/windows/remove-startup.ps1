# Remove the Trailarr Task Scheduler startup task.

Stop-ScheduledTask      -TaskName "Trailarr" -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "Trailarr" -Confirm:$false -ErrorAction SilentlyContinue

Write-Host "Trailarr startup task removed."
