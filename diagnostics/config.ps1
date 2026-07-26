$Global:Config = @{

    Duration = 150

    ArtifactRoot = "$PSScriptRoot\artifacts"

    Collectors = @{

        Docker = @{
            Enabled = $true
            Interval = 1
        }

        Nginx = @{
            Enabled = $true
            Interval = 1
        }

        Postgres = @{
            Enabled = $true
            Interval = 2
        }

        Sockets = @{
            Enabled = $true
            Interval = 1
        }

        PySpy = @{
            Enabled = $true
            Delay = 30
            Duration = 30
        }

    }

    Containers = @{

        Backend1  = "eri-backend-1"
        Backend2  = "eri-backend-2"
        Nginx     = "eri-nginx"
        Postgres  = "exam_db"
        PgBouncer = "eri-pgbouncer"

    }

    Database = @{

        User = "exam_user"
        Name = "exam_platform"

    }

}