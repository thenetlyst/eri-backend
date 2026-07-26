param(
    [string]$Container,
    [string]$ArtifactDir,
    [int]$Delay = 30,
    [int]$Duration = 30
)

Start-Sleep -Seconds $Delay

$svg = "/tmp/pyspy.svg"

Write-Host ""
Write-Host "========================================"
Write-Host "Profiling $Container"
Write-Host "========================================"

$output = docker exec `
    $Container `
    py-spy `
    record `
    --pid 1 `
    --subprocesses `
    --duration $Duration `
    --output $svg 2>&1

$output | Write-Host

if ($LASTEXITCODE -ne 0) {
    throw "py-spy failed."
}

docker exec $Container ls -lh $svg

docker cp `
    "${Container}:${svg}" `
    (Join-Path $ArtifactDir "$Container-pyspy.svg")

docker exec $Container rm -f $svg

Write-Host "Finished profiling $Container"