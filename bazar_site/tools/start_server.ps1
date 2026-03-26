$ErrorActionPreference = "Stop"

$ProjectDir = "C:\Users\Louis\Documents\01\bazar_site"
$LogsDir = Join-Path $ProjectDir "tools\run-logs"
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

$PgBin = "C:\Users\Louis\Desktop\pgsql\bin"
$PgData = "C:\Users\Louis\Documents\pgdata"
$PgLog = Join-Path $LogsDir "postgres.log"

$Python = "python"
$Cloudflared = "C:\Users\Louis\Documents\01\tools\cloudflared.exe"

$RunserverHost = "127.0.0.1"
$RunserverPort = 8000
$RunserverUrl = "http://$RunserverHost`:$RunserverPort"

$PgPidFile = Join-Path $LogsDir "postgres.pid"
$DjangoPidFile = Join-Path $LogsDir "django.pid"
$TunnelPidFile = Join-Path $LogsDir "tunnel.pid"

function Write-Info([string]$msg) {
  $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  Write-Host "[$ts] $msg"
}

function Save-Pid([string]$path, [int]$procId) {
  Set-Content -Path $path -Value $procId -Encoding ascii
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

function Ensure-PostgresStarted() {
  if (!(Test-Path (Join-Path $PgBin "pg_ctl.exe"))) {
    throw "PostgreSQL not found at $PgBin. Expected pg_ctl.exe."
  }
  if (!(Test-Path $PgData)) {
    throw "PostgreSQL data dir not found at $PgData."
  }

  Write-Info "Checking PostgreSQL status..."
  & (Join-Path $PgBin "pg_ctl.exe") -D $PgData status *> $null
  if ($LASTEXITCODE -eq 0) {
    Write-Info "PostgreSQL is already running."
    return
  }

  Write-Info "Starting PostgreSQL..."
  # pg_ctl on Windows can take a while; run via cmd to avoid PowerShell stream quirks.
  cmd /c "\"$PgBin\\pg_ctl.exe\" -D \"$PgData\" -l \"$PgLog\" start" | Out-Null
  Start-Sleep -Seconds 2

  & (Join-Path $PgBin "pg_ctl.exe") -D $PgData status *> $null
  if ($LASTEXITCODE -ne 0) {
    throw "PostgreSQL failed to start. Check log: $PgLog"
  }
  Write-Info "PostgreSQL started."
}

function Ensure-PortFree([int]$port) {
  $lines = cmd /c "netstat -ano | findstr :$port"
  foreach ($line in $lines) {
    if ($line -match "LISTENING\s+(\d+)$") {
      $procId = [int]$Matches[1]
      try {
        $p = Get-Process -Id $procId -ErrorAction Stop
        Write-Info "Port $port is in use by $($p.ProcessName) (pid=$procId). Stopping it..."
        Stop-Process -Id $procId -Force
      } catch {
        # ignore
      }
    }
  }
}

function Start-Django() {
  Write-Info "Starting Django dev server at $RunserverUrl ..."
  Ensure-PortFree $RunserverPort

  $djangoOut = Join-Path $LogsDir "django.out.log"
  $djangoErr = Join-Path $LogsDir "django.err.log"
  Write-Info "Django logs: $djangoOut / $djangoErr"
  if (!(Test-Path $djangoOut)) { New-Item -ItemType File -Path $djangoOut | Out-Null }
  if (!(Test-Path $djangoErr)) { New-Item -ItemType File -Path $djangoErr | Out-Null }

  $p = Start-Process -FilePath $Python `
    -ArgumentList @("manage.py","runserver","$RunserverHost`:$RunserverPort") `
    -WorkingDirectory $ProjectDir `
    -PassThru `
    -WindowStyle Normal `
    -RedirectStandardOutput $djangoOut `
    -RedirectStandardError $djangoErr

  Save-Pid $DjangoPidFile $p.Id
  Start-Sleep -Seconds 2
  Write-Info "Django started (pid=$($p.Id))."
}

function Start-Tunnel() {
  if (!(Test-Path $Cloudflared)) {
    throw "cloudflared.exe not found at $Cloudflared"
  }
  Write-Info "Starting Cloudflare quick tunnel..."
  $tunnelOut = Join-Path $LogsDir "tunnel.out.log"
  $tunnelErr = Join-Path $LogsDir "tunnel.err.log"
  Write-Info "Tunnel logs: $tunnelOut / $tunnelErr"
  if (!(Test-Path $tunnelOut)) { New-Item -ItemType File -Path $tunnelOut | Out-Null }
  if (!(Test-Path $tunnelErr)) { New-Item -ItemType File -Path $tunnelErr | Out-Null }

  $p = Start-Process -FilePath $Cloudflared `
    -ArgumentList @("tunnel","--url",$RunserverUrl) `
    -WorkingDirectory $ProjectDir `
    -PassThru `
    -WindowStyle Normal `
    -RedirectStandardOutput $tunnelOut `
    -RedirectStandardError $tunnelErr

  Save-Pid $TunnelPidFile $p.Id
  Start-Sleep -Seconds 5

  # Try to print the public URL from the log.
  $url = $null
  foreach ($pLog in @($tunnelOut, $tunnelErr)) {
    if ($url) { break }
    if (Test-Path $pLog) {
      $m = Select-String -Path $pLog -Pattern "https://[a-z0-9-]+\\.trycloudflare\\.com" -AllMatches -ErrorAction SilentlyContinue |
        Select-Object -Last 1
      if ($m -and $m.Matches.Count -gt 0) { $url = $m.Matches[0].Value }
    }
  }

  if ($url) {
    Write-Info "Tunnel URL: $url"
  } else {
    Write-Info "Tunnel started (pid=$($p.Id)). Check tunnel.out.log for URL."
  }
}

Write-Info "=== START SERVER ==="
Write-Info "Logs: $LogsDir"
Write-Info "Project: $ProjectDir"

# If previous processes were recorded, stop them first to avoid conflicts.
Stop-IfRunning $TunnelPidFile "Tunnel"
Stop-IfRunning $DjangoPidFile "Django"

Ensure-PostgresStarted
Start-Django
Start-Tunnel

Write-Info "Done."
