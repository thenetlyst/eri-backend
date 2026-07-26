param(
    [string]$Artifact,
    [int]$Interval
)

while (-not (Test-Path "$Artifact\stop.signal"))
{
    try
    {
        docker stats `
        --no-stream `
        --format json `
        eri-backend-1 `
        eri-backend-2 `
        eri-nginx `
        exam_db `
        eri-pgbouncer |
        Add-Content "$Artifact\docker_stats.jsonl"
    }
    catch
    {
        @{
            ts = Get-Date -Format o
            collector = "docker_stats"
            error = $_.Exception.Message
        } |
        ConvertTo-Json -Compress |
        Add-Content "$Artifact\collector_errors.jsonl"
    }

    Start-Sleep $Interval
}