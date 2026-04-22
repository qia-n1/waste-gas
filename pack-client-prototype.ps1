param(
  [string]$OutDir = "release",
  [string]$Name = ""
)

$ErrorActionPreference = "Stop"

Push-Location $PSScriptRoot
try {
  if (-not (Test-Path $OutDir)) {
    New-Item -ItemType Directory -Path $OutDir | Out-Null
  }

  $stamp = Get-Date -Format "yyyyMMdd-HHmm"
  if ([string]::IsNullOrWhiteSpace($Name)) {
    $Name = "waste-gas-client-prototype-$stamp.zip"
  }
  $zipPath = Join-Path $OutDir $Name

  if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
  }

  $required = @(
    "docker-compose.client.yml",
    "CLIENT_PROTOTYPE.md",
    "run-client-prototype.ps1",
    "stop-client-prototype.ps1",
    "client-backend",
    "client-frontend"
  )

  foreach ($p in $required) {
    if (-not (Test-Path $p)) { throw "Missing path: $p" }
  }

  $tmpRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("waste-gas-client-prototype-" + $stamp)
  if (Test-Path $tmpRoot) { Remove-Item $tmpRoot -Recurse -Force }
  New-Item -ItemType Directory -Path $tmpRoot | Out-Null

  $stage = Join-Path $tmpRoot "pkg"
  New-Item -ItemType Directory -Path $stage | Out-Null

  Copy-Item "docker-compose.client.yml" -Destination $stage -Force
  Copy-Item "CLIENT_PROTOTYPE.md" -Destination $stage -Force
  Copy-Item "run-client-prototype.ps1" -Destination $stage -Force
  Copy-Item "stop-client-prototype.ps1" -Destination $stage -Force
  Copy-Item "client-backend" -Destination $stage -Recurse -Force
  Copy-Item "client-frontend" -Destination $stage -Recurse -Force

  # Keep the package safe and lightweight for delivery.
  # - Remove .env (ship .env.example instead)
  # - Remove Python bytecode caches
  # - Remove local demo DB (compose uses volume-created DB at runtime)
  $maybeEnv = Join-Path $stage "client-backend/.env"
  if (Test-Path $maybeEnv) { Remove-Item $maybeEnv -Force }

  Get-ChildItem -Path (Join-Path $stage "client-backend") -Recurse -Force -Directory -Filter "__pycache__" |
    ForEach-Object { Remove-Item $_.FullName -Recurse -Force }
  Get-ChildItem -Path (Join-Path $stage "client-backend") -Recurse -Force -File -Filter "*.pyc" |
    ForEach-Object { Remove-Item $_.FullName -Force }

  $maybeDb = Join-Path $stage "client-backend/vocs.db"
  if (Test-Path $maybeDb) { Remove-Item $maybeDb -Force }

  Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zipPath

  Remove-Item $tmpRoot -Recurse -Force
  Write-Host "OK: $zipPath"
} finally {
  Pop-Location
}

