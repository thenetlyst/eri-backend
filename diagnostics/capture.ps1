$ErrorActionPreference = "Continue"

. "$PSScriptRoot\config.ps1"
. "$PSScriptRoot\helpers.ps1"

$artifactDir = New-ArtifactFolder $Config.ArtifactRoot

@{
    started = Get-Date -Format o
    duration = $Config.Duration
    collector_intervals = $Config.Collectors
    computer = $env:COMPUTERNAME
    user = $env:USERNAME
    diagnostics_version = "0.1"
} |
ConvertTo-Json |
Out-File "$artifactDir\run.json"

Write-Host ""
Write-Host "====================================="
Write-Host "ERI Diagnostics Flight Recorder"
Write-Host "====================================="
Write-Host ""
Write-Host "Artifact directory:"
Write-Host $artifactDir
Write-Host ""


$jobs = @()

# Docker Stats
if ($Config.Collectors.Docker.Enabled)
{
    $jobs += Start-Collector `
        -Name "DockerStats" `
        -Script "$PSScriptRoot\collectors\docker_stats.ps1" `
        -Arguments @(
            $artifactDir,
            $Config.Collectors.Docker.Interval
        )
}

# Nginx Status
if ($Config.Collectors.Nginx.Enabled)
{
    $jobs += Start-Collector `
        -Name "NginxStatus" `
        -Script "$PSScriptRoot\collectors\nginx_status.ps1" `
        -Arguments @(
            $artifactDir,
            $Config.Containers.Nginx,
            $Config.Collectors.Nginx.Interval
        )
}

# PostgreSQL
if ($Config.Collectors.Postgres.Enabled)
{
    $jobs += Start-Collector `
        -Name "Postgres" `
        -Script "$PSScriptRoot\collectors\postgres.ps1" `
        -Arguments @(
            $artifactDir,
            $Config.Containers.Postgres,
            $Config.Database.User,
            $Config.Database.Name,
            $Config.Collectors.Postgres.Interval
        )
}


# TCP Socket States
if ($Config.Collectors.Sockets.Enabled)
{
    $jobs += Start-Collector `
        -Name "Sockets" `
        -Script "$PSScriptRoot\collectors\sockets.ps1" `
        -Arguments @(
            $artifactDir,
            $Config.Collectors.Sockets.Interval
        )
}


$jobs += Start-Job `
    -ArgumentList $pySpyScript, $artifactDir `
    -ScriptBlock {

    param(
        $Script,
        $ArtifactDir
    )

    & $Script `
        -Container "eri-backend-1" `
        -ArtifactDir $ArtifactDir `
        -Delay 30 `
        -Duration 60
}

$jobs += Start-Job `
    -ArgumentList $pySpyScript, $artifactDir `
    -ScriptBlock {

    param(
        $Script,
        $ArtifactDir
    )

    & $Script `
        -Container "eri-backend-2" `
        -ArtifactDir $ArtifactDir `
        -Delay 30 `
        -Duration 60
}

Write-Host ""
Write-Host "Collectors Started"
Write-Host "------------------"

Get-Job |
    Select-Object Id, Name, State |
    Format-Table -AutoSize

Write-Host ""

Start-Sleep $Config.Duration

Write-Host ""
Write-Host "Stopping collectors..."
Write-Host ""

New-Item `
    "$artifactDir\stop.signal" `
    -ItemType File `
    -Force | Out-Null

Wait-Job $jobs -Timeout 30 | Out-Null

$running = Get-Job | Where-Object State -eq "Running"

if ($running)
{
    Write-Warning "Some collectors did not exit cleanly."

    $running | Stop-Job -Force
}

Remove-Job *

Save-DockerLogs $Config.Containers.Backend1 "$artifactDir\backend1.log"
Save-DockerLogs $Config.Containers.Backend2 "$artifactDir\backend2.log"
Save-DockerLogs $Config.Containers.Nginx "$artifactDir\nginx.log"
Save-DockerLogs $Config.Containers.Postgres "$artifactDir\postgres.log"
Save-DockerLogs $Config.Containers.PgBouncer "$artifactDir\pgbouncer.log"

@{
    finished = Get-Date -Format o
} |
ConvertTo-Json |
Out-File "$artifactDir\run_complete.json"


if (Test-Path "$artifactDir.zip") {
    Remove-Item "$artifactDir.zip" -Force
}

Compress-Archive `
    -Path "$artifactDir\*" `
    -DestinationPath "$artifactDir.zip"

Write-Host ""
Write-Host "====================================="
Write-Host "Capture complete"
Write-Host "====================================="
Write-Host ""

Write-Host "Artifacts:"
Write-Host $artifactDir

Write-Host ""
Write-Host "Archive:"
Write-Host "$artifactDir.zip"

