$examDayId = "dca66be8-440f-43ab-9a4f-aa9254ed73db"

$users = 1..20 | ForEach-Object { "load$_@eri.local" }

$jobs = foreach ($email in $users) {
    Start-Job -ScriptBlock {

        param($email, $examDayId)

        $loginBody = @{ email = $email } | ConvertTo-Json

        $login = Invoke-RestMethod `
            -Uri "http://localhost:8000/auth/dev-login" `
            -Method Post `
            -Headers @{ "x-dev-key" = "ERI_DEV_LOGIN" } `
            -Body $loginBody `
            -ContentType "application/json"

        $token = $login.access_token

        $headers = @{
            Authorization = "Bearer $token"
        }

        $body = @{
            exam_day_id = $examDayId
        } | ConvertTo-Json

        Invoke-RestMethod `
            -Uri "http://localhost:8000/attempts/start" `
            -Method Post `
            -Headers $headers `
            -Body $body `
            -ContentType "application/json"

    } -ArgumentList $email, $examDayId
}

Wait-Job $jobs
Receive-Job $jobs