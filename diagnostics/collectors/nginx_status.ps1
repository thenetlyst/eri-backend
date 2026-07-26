param(
    [string]$Artifact,
    [string]$Container,
    [int]$Interval
)

while (-not (Test-Path "$Artifact\stop.signal"))
{
    try
    {
        $status = docker exec $Container curl -s http://localhost/nginx_status

        if ($LASTEXITCODE -eq 0 -and $status)
        {
            $lines = $status -split "`n"

            $last = ($lines | Where-Object { $_ -match "^Reading:" })

            if ($last)
            {
                $parts = $last -split "\s+"

                @{
                    ts = Get-Date -Format o
                    active = [int](($lines[0] -split ":")[1].Trim())
                    reading = [int]$parts[1]
                    writing = [int]$parts[3]
                    waiting = [int]$parts[5]
                } |
                ConvertTo-Json -Compress |
                Add-Content "$Artifact\nginx_status.jsonl"
            }
        }
    }
    catch
    {
        @{
            ts = Get-Date -Format o
            collector = "nginx_status"
            error = $_.Exception.Message
        } |
        ConvertTo-Json -Compress |
        Add-Content "$Artifact\collector_errors.jsonl"
    }

    Start-Sleep $Interval
}