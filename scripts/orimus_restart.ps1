$ErrorActionPreference = "Stop"

$requestedModes = @()
foreach ($argument in $args) {
    if ($argument -eq "--soft" -or $argument -eq "-Soft") {
        $requestedModes += "soft"
    } elseif ($argument -eq "--hard" -or $argument -eq "-Hard") {
        $requestedModes += "hard"
    } else {
        Write-Error "Usage: scripts/orimus_restart.ps1 [--soft|--hard]"
    }
}

if ($requestedModes.Count -gt 1) {
    Write-Error "Choose either --soft or --hard, not both."
}

if ($requestedModes.Count -eq 0) {
    $requestedModes += "soft"
}

$mode = $requestedModes[0]
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

function Restart-OrimusServices {
    docker compose down
    docker compose up -d --build backend ros2-dev
}

if ($mode -eq "soft") {
    Write-Host "ORIMUS soft restart: restarting services while preserving mission history, artifacts, and audit data."
    Restart-OrimusServices
    exit 0
}

Write-Host "ORIMUS hard restart: wiping demo SQLite/artifacts/latest report, then restarting services."

$pathsToRemove = @(
    "data\orimus.db",
    "data\artifacts",
    "reports\latest_mission_report.json"
)

foreach ($relativePath in $pathsToRemove) {
    $target = Join-Path $repoRoot $relativePath
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}

New-Item -ItemType Directory -Force -Path (Join-Path $repoRoot "data\artifacts") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $repoRoot "reports") | Out-Null

Restart-OrimusServices
