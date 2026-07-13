\set ON_ERROR_STOP on

BEGIN;

-- ============================================================
-- REQUIRED VARIABLES
--
-- Pass using:
--
-- -v exam_day_id="'<uuid>'"
-- -v start_user=60
-- -v end_user=84
-- ============================================================

DROP TABLE IF EXISTS reset_attempts;

CREATE TEMP TABLE reset_attempts AS
SELECT
    a.id,
    u.firebase_uid,
    a.status
FROM attempts a
JOIN participants p
    ON p.id = a.participant_id
JOIN users u
    ON u.id = p.user_id
WHERE
    a.exam_day_id = :'exam_day_id'
    AND CAST(
        REPLACE(
            u.firebase_uid,
            'dev-user-',
            ''
        ) AS INTEGER
    )
    BETWEEN :start_user
        AND :end_user;

-- ============================================================
-- SUMMARY
-- ============================================================

SELECT
    COUNT(*) AS attempts_found
FROM reset_attempts;

SELECT
    firebase_uid,
    status
FROM reset_attempts
ORDER BY
    CAST(
        REPLACE(
            firebase_uid,
            'dev-user-',
            ''
        ) AS INTEGER
    );

-- ============================================================
-- SAFETY CHECK
-- ======================================================
-- ============================================================
-- SAFETY CHECK
-- ============================================================

SELECT
    COUNT(*) AS attempts_found
FROM reset_attempts;

-- ============================================================
-- DELETE CHILD TABLES
-- ============================================================

DELETE FROM attempt_answers
WHERE attempt_id IN (
    SELECT id
    FROM reset_attempts
);

DELETE FROM responses
WHERE attempt_id IN (
    SELECT id
    FROM reset_attempts
);

DELETE FROM attempt_events
WHERE attempt_id IN (
    SELECT id
    FROM reset_attempts
);

-- ============================================================
-- DELETE ATTEMPTS
-- ============================================================

DELETE FROM attempts
WHERE id IN (
    SELECT id
    FROM reset_attempts
);

-- ============================================================
-- VERIFY
-- ============================================================

SELECT
    COUNT(*) AS remaining_attempts
FROM attempts
WHERE id IN (
    SELECT id
    FROM reset_attempts

);

COMMIT;

\echo
\echo ============================================
\echo Attempt reset completed successfully.
\echo ============================================