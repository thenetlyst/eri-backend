param(
    [string]$Artifact,
    [int]$Interval = 1
)

$helper = Join-Path $PSScriptRoot "..\helpers.ps1"
. $helper

$stopFile = Join-Path $Artifact "stop.signal"

while (-not (Test-Path $stopFile))
{
    try
    {
        $connections = Get-NetTCPConnection -ErrorAction Stop

        $counts = @{}

        foreach ($group in ($connections | Group-Object State))
        {
            $counts[$group.Name] = $group.Count
        }

        @{
            ts = Get-Date -Format o
            collector = "sockets"
            data = $counts
        } |
        ConvertTo-Json -Compress |
        Add-Content "$Artifact\sockets.jsonl"
    }
    catch
    {
        @{
            ts = Get-Date -Format o
            collector = "sockets"
            error = $_.Exception.Message
        } |
        ConvertTo-Json -Compress |
        Add-Content "$Artifact\collector_errors.jsonl"
    }

    Start-Sleep -Seconds $Interval
}