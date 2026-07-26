function Get-Timestamp {
    return (Get-Date).ToString("o")
}

function New-ArtifactFolder {

    param([string]$Root)

    $name = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"

    $path = Join-Path $Root $name

    New-Item -ItemType Directory -Path $path -Force | Out-Null

    return $path
}

function Write-JsonLine {

    param(
        [string]$Path,
        [object]$Object
    )

    $Object | ConvertTo-Json -Compress | Add-Content $Path
}

function Save-DockerLogs {

    param(
        [string]$Container,
        [string]$OutputFile
    )

    try {
        docker logs $Container --since=5m *> $OutputFile 2>$null
    }
    catch {
        Write-Warning "Failed to collect logs for $Container"
    }
}

function Start-Collector {

    param(
        [string]$Name,
        [string]$Script,
        [object[]]$Arguments
    )

    return Start-Job `
        -Name $Name `
        -FilePath $Script `
        -ArgumentList $Arguments
}