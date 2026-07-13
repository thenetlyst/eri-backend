\set ON_ERROR_STOP on

SELECT
    u.firebase_uid,
    u.email
FROM users u
JOIN participants p
    ON p.user_id = u.id
LEFT JOIN attempts a
    ON a.participant_id = p.id
   AND a.exam_day_id = :'exam_day_id'
WHERE
    a.id IS NULL
    AND CAST(
        REPLACE(
            u.firebase_uid,
            'dev-user-',
            ''
        ) AS INTEGER
    )
    BETWEEN :start_user
        AND :end_user
ORDER BY
    CAST(
        REPLACE(
            u.firebase_uid,
            'dev-user-',
            ''
        ) AS INTEGER
    );