$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$dockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"

function Test-Command($name) {
  $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

function Stop-WorkspaceListener($port, $pathNeedle) {
  $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  foreach ($listener in $listeners) {
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $($listener.OwningProcess)" -ErrorAction SilentlyContinue
    if ($proc -and $proc.CommandLine -like "*$pathNeedle*") {
      Stop-Process -Id $listener.OwningProcess -Force -ErrorAction SilentlyContinue
    }
  }
}

function Wait-Docker() {
  if (-not (Test-Command "docker")) {
    throw "Docker CLI was not found. Install Docker Desktop, then rerun this script."
  }

  docker info *> $null
  if ($LASTEXITCODE -ne 0) {
    if (-not (Test-Path $dockerDesktop)) {
      throw "Docker Desktop is not running, and Docker Desktop was not found at $dockerDesktop."
    }
    Write-Host "Starting Docker Desktop..."
    Start-Process -WindowStyle Hidden -FilePath $dockerDesktop
  }

  for ($i = 0; $i -lt 40; $i++) {
    docker info *> $null
    if ($LASTEXITCODE -eq 0) { return }
    Start-Sleep -Seconds 3
  }

  throw "Docker did not become ready in time. Open Docker Desktop and rerun this script."
}

Write-Host "Starting Ethara local stack..."
Wait-Docker

Push-Location $root
try {
  docker compose up -d postgres
  for ($i = 0; $i -lt 30; $i++) {
    $status = docker inspect --format='{{.State.Health.Status}}' ethara-postgres 2>$null
    if ($status -eq "healthy") { break }
    Start-Sleep -Seconds 2
  }
} finally {
  Pop-Location
}

Stop-WorkspaceListener 8020 $backendDir
Stop-WorkspaceListener 3000 $frontendDir
Start-Sleep -Seconds 2

Start-Process -WindowStyle Hidden -WorkingDirectory $backendDir `
  -FilePath (Join-Path $backendDir "venv\Scripts\python.exe") `
  -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8020" `
  -RedirectStandardOutput (Join-Path $backendDir "uvicorn-8020.log") `
  -RedirectStandardError (Join-Path $backendDir "uvicorn-8020.err.log")

Start-Process -WindowStyle Hidden -WorkingDirectory $frontendDir `
  -FilePath "npm.cmd" `
  -ArgumentList "run", "dev", "--", "-p", "3000" `
  -RedirectStandardOutput (Join-Path $frontendDir "next-3000.log") `
  -RedirectStandardError (Join-Path $frontendDir "next-3000.err.log")

Write-Host "Ethara is starting. Open http://localhost:3000"
Write-Host "Backend API: http://127.0.0.1:8020"