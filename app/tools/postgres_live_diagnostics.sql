-- Active sessions
SELECT
    now(),
    pid,
    usename,
    application_name,
    state,
    wait_event_type,
    wait_event,
    backend_start,
    xact_start,
    query_start,
    state_change,
    LEFT(query, 300) AS query
FROM pg_stat_activity
WHERE datname = current_database()
ORDER BY query_start NULLS LAST;

-- Blocking relationships
SELECT
    blocked.pid AS blocked_pid,
    blocker.pid AS blocker_pid,
    blocked.wait_event_type,
    blocked.wait_event,
    LEFT(blocked.query,150) AS blocked_query,
    LEFT(blocker.query,150) AS blocker_query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocker
ON blocker.pid = ANY(pg_blocking_pids(blocked.pid));

-- Lock summary
SELECT
    mode,
    granted,
    COUNT(*)
FROM pg_locks
GROUP BY mode, granted
ORDER BY mode;

-- Long transactions
SELECT
    pid,
    now() - xact_start AS transaction_age,
    state,
    LEFT(query,300)
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
ORDER BY transaction_age DESC;