param(
    [Parameter(Mandatory = $true)]
    [string]$RunName
)

$OutputDir = ".\pq\results\$RunName"

if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
}

Write-Host ""
Write-Host "======================================="
Write-Host "Starting PQ Collectors"
Write-Host "Run : $RunName"
Write-Host "Folder : $OutputDir"
Write-Host "======================================="
Write-Host ""

# -------------------------------------------------------
# Docker Stats
# -------------------------------------------------------

Start-Process powershell `
-ArgumentList @(
"-NoExit",
"-Command",
@"
while (`$true) {
    `$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff'

    docker stats --no-stream --format "{{.Name}},{{.CPUPerc}},{{.MemPerc}},{{.MemUsage}},{{.NetIO}}" |
    ForEach-Object {
        "`$ts,`$_"
    } |
    Out-File -Append "$OutputDir\docker_stats.csv"

    Start-Sleep 1
}
"@
)

# -------------------------------------------------------
# Backend 1 Logs
# -------------------------------------------------------

Start-Process powershell `
-ArgumentList @(
"-NoExit",
"-Command",
"docker compose logs -f eri-backend-1 | Tee-Object '$OutputDir\backend1.log'"
)

# -------------------------------------------------------
# Backend 2 Logs
# -------------------------------------------------------

Start-Process powershell `
-ArgumentList @(
"-NoExit",
"-Command",
"docker compose logs -f eri-backend-2 | Tee-Object '$OutputDir\backend2.log'"
)

Write-Host ""
Write-Host "Collectors started."
Write-Host ""