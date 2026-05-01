# Trailarr startup wrapper — runs as the logged-in user so mapped network
# drives and user-session resources are accessible.
# Called by the Task Scheduler task created by setup-startup.ps1.

$InstallDir = "C:\Program Files\Trailarr"
$DataDir    = "C:\ProgramData\Trailarr"
$LogFile    = "$DataDir\logs\trailarr.log"

$env:APP_DATA_DIR  = $DataDir
$env:PYTHONPATH    = "$InstallDir\backend"
$env:PYTHONUTF8    = "1"

& "$InstallDir\backend\.venv\Scripts\trailarr.exe" `
    "$InstallDir\scripts\start\start.py" *>> $LogFile
