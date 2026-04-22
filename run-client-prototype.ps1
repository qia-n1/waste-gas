param(
  [switch]$NoBuild
)

$ErrorActionPreference = "Stop"

Write-Host "== Waste Gas Client Prototype =="
Write-Host "Working dir: $PSScriptRoot"

Push-Location $PSScriptRoot
try {
  Write-Host ""
  Write-Host "Checking Docker daemon..."
  $originalContext = ""
  try { $originalContext = (docker context show).Trim() } catch { $originalContext = "" }
  $hasDesktopLinux = $false
  try {
    $ctx = docker context ls --format "{{.Name}}"
    $hasDesktopLinux = ($ctx -split "`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -eq "desktop-linux" } | Measure-Object).Count -gt 0
  } catch {
    $hasDesktopLinux = $false
  }

  if ($hasDesktopLinux -and $originalContext -ne "desktop-linux") {
    Write-Host "Switching docker context: $originalContext -> desktop-linux"
    docker context use desktop-linux *> $null
  }

  docker version *> $null

  Write-Host ""
  Write-Host "Checking registry connectivity (docker.io)..."
  Write-Host "If this step fails, configure Docker Desktop HTTPS proxy or allow registry-1.docker.io:443."
  try {
    docker pull redis:7-alpine *> $null
  } catch {
    Write-Host ""
    Write-Host "ERROR: Cannot pull from Docker Hub (registry-1.docker.io:443)."
    Write-Host "Fix options:"
    Write-Host "  - Docker Desktop -> Settings -> Resources -> Proxies: set BOTH HTTP+HTTPS proxy"
    Write-Host "  - Ensure your network allows registry-1.docker.io:443 (IPv4/IPv6 both if possible)"
    throw
  }

  if (-not $NoBuild) {
    Write-Host ""
    Write-Host "Building and starting containers..."
    docker compose -f docker-compose.client.yml up -d --build
  } else {
    Write-Host ""
    Write-Host "Starting containers (no build)..."
    docker compose -f docker-compose.client.yml up -d
  }

  Write-Host ""
  docker compose -f docker-compose.client.yml ps

  Write-Host ""
  Write-Host "Open in browser:"
  Write-Host "  Frontend: http://localhost:8080"
  Write-Host "  Backend health: http://localhost:8002/api/v1/health"
  Write-Host ""
  Write-Host "Tip: If API health is not ready yet, wait 5-15s and refresh."
} finally {
  try {
    if ($originalContext -and $originalContext -ne "desktop-linux") {
      docker context use $originalContext *> $null
    }
  } catch {
    # ignore context restore failures
  }
  Pop-Location
}

