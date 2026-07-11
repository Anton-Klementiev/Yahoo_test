# scripts/run_ingest.ps1
# Runs the daily NASDAQ-100 consensus ingestion, unattended.
# Called by Windows Task Scheduler; can also be run by hand to test.

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python  = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$OutLog  = Join-Path $ProjectRoot "logs\scheduler.out.log"
$ErrLog  = Join-Path $ProjectRoot "logs\scheduler.err.log"
$Wrapper = Join-Path $ProjectRoot "logs\scheduler.log"

Add-Content -Path $Wrapper -Value "$(Get-Date -Format o)  Starting ingestion" -Encoding utf8

$proc = Start-Process -FilePath $Python `
    -ArgumentList "-m", "src.ingest" `
    -WorkingDirectory $ProjectRoot `
    -NoNewWindow -Wait -PassThru `
    -RedirectStandardOutput $OutLog `
    -RedirectStandardError  $ErrLog

$code = $proc.ExitCode
Add-Content -Path $Wrapper -Value "$(Get-Date -Format o)  Finished with exit code $code" -Encoding utf8
exit $code