$ErrorActionPreference = "Stop"

$ProjectDir = "C:\Users\Louis\Documents\01\bazar_site"
$LogsDir = Join-Path $ProjectDir "tools\run-logs"

$PgBin = "C:\Users\Louis\Desktop\pgsql\bin"
$PgData = "C:\Users\Louis\Documents\pgdata"

$DjangoPidFile = Join-Path $LogsDir "django.pid"
$TunnelPidFile = Join-Path $LogsDir "tunnel.pid"

function Write-Info([string]$msg) {
  $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  Write-Host "[$ts] $msg"
}

function Read-Pid([string]$path) {
  if (!(Test-Path $path)) { return $null }
  $raw = (Get-Content -Path $path -ErrorAction SilentlyContinue | Select-Object -First 1)
  if (!$raw) { return $null }
  try { return [int]$raw } catch { return $null }
}

function Stop-IfRunning([string]$pidFile, [string]$name) {
  $procId = Read-Pid $pidFile
  if ($procId -eq $null) { return }
  try {
    $p = Get-Process -Id $procId -ErrorAction Stop
    Write-Info "Stopping $name (pid=$procId)..."
    Stop-Process -Id $procId -Force
  } catch {
    # already stopped
  }
  Remove-Item -Force -ErrorAction SilentlyContinue $pidFile | Out-Null
}

Write-Info "=== STOP SERVER ==="

Stop-IfRunning $TunnelPidFile "Tunnel"
Stop-IfRunning $DjangoPidFile "Django"

if (Test-Path (Join-Path $PgBin "pg_ctl.exe")) {
  try {
    Write-Info "Stopping PostgreSQL..."
    & (Join-Path $PgBin "pg_ctl.exe") -D $PgData stop | Out-Null
  } catch {
    Write-Info "PostgreSQL stop skipped (maybe not running)."
  }
}

Write-Info "Done."

