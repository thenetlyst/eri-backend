param(
    [string]$Artifact,
    [string]$Container,
    [string]$User,
    [string]$Database,
    [int]$Interval
)

$query = @"
SELECT json_build_object(
    'active', COUNT(*) FILTER (WHERE state='active'),
    'idle', COUNT(*) FILTER (WHERE state='idle'),
    'idle_in_tx', COUNT(*) FILTER (WHERE state='idle in transaction'),
    'waiting', COUNT(*) FILTER (WHERE wait_event IS NOT NULL),
    'total', COUNT(*)
)
FROM pg_stat_activity;
"@

while (-not (Test-Path "$Artifact\stop.signal"))
{
    try
    {
        $result = docker exec $Container `
            psql `
            -U $User `
            -d $Database `
            -t `
            -A `
            -c $query

        $result = ($result -join "").Trim()

        if ($result)
        {
            $json = $result | ConvertFrom-Json

            @{
                ts = Get-Date -Format o
                collector = "postgres"
                data = $json
            } |
            ConvertTo-Json -Compress |
            Add-Content "$Artifact\postgres.jsonl"
        }
    }
    catch
    {
        @{
            ts = Get-Date -Format o
            collector = "postgres"
            error = $_.Exception.Message
        } |
        ConvertTo-Json -Compress |
        Add-Content "$Artifact\collector_errors.jsonl"
    }

    Start-Sleep $Interval
}