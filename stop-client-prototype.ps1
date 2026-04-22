$ErrorActionPreference = "Stop"

Write-Host "Stopping client prototype containers (keeping volumes)..."

Push-Location $PSScriptRoot
try {
  docker compose -f docker-compose.client.yml down
  docker compose -f docker-compose.client.yml ps
} finally {
  Pop-Location
}

