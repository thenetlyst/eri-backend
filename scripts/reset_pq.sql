BEGIN;

TRUNCATE TABLE
    attempt_events,
    attempt_answers,
    attempts,
    participant_progress,
    rankings,
    institution_rankings
RESTART IDENTITY CASCADE;

UPDATE exam_days
SET
    window_start = NOW() - INTERVAL '1 hour',
    window_end   = NOW() + INTERVAL '12 hours';

COMMIT;