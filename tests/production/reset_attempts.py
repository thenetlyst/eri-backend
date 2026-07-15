#!/usr/bin/env python3

import argparse
import sys

import psycopg2


def main():
    parser = argparse.ArgumentParser(
        description="Reset load-test attempts for a range of dev users."
    )

    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5432)
    parser.add_argument("--database", default="exam_platform")
    parser.add_argument("--user", default="exam_user")
    parser.add_argument("--password", default="exam_password")

    parser.add_argument("--exam-day", required=True)
    parser.add_argument("--start-user", type=int, required=True)
    parser.add_argument("--end-user", type=int, required=True)

    args = parser.parse_args()

    conn = psycopg2.connect(
        host=args.host,
        port=args.port,
        dbname=args.database,
        user=args.user,
        password=args.password,
    )

    conn.autocommit = False

    try:
        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    COUNT(*)
                FROM attempts a
                JOIN participants p
                    ON p.id = a.participant_id
                JOIN users u
                    ON u.id = p.user_id
                WHERE
                    a.exam_day_id = %s
                    AND CAST(
                        REPLACE(
                            u.firebase_uid,
                            'dev-user-',
                            ''
                        ) AS INTEGER
                    )
                    BETWEEN %s AND %s
                """,
                (
                    args.exam_day,
                    args.start_user,
                    args.end_user,
                ),
            )

            count = cur.fetchone()[0]

            print()
            print("===================================")
            print("Attempts found :", count)
            print("Exam Day       :", args.exam_day)
            print(
                f"User Range     : {args.start_user}-{args.end_user}"
            )
            print("===================================")
            print()

            if count == 0:
                print("Nothing to delete.")
                conn.rollback()
                return

            answer = input("Delete these attempts? (yes/no): ")

            if answer.lower() != "yes":
                conn.rollback()
                print("Cancelled.")
                return

            delete_sql = """
            WITH target_attempts AS (
                SELECT
                    a.id
                FROM attempts a
                JOIN participants p
                    ON p.id = a.participant_id
                JOIN users u
                    ON u.id = p.user_id
                WHERE
                    a.exam_day_id = %s
                    AND CAST(
                        REPLACE(
                            u.firebase_uid,
                            'dev-user-',
                            ''
                        ) AS INTEGER
                    )
                    BETWEEN %s AND %s
            )

            DELETE FROM attempt_answers
            WHERE attempt_id IN (
                SELECT id FROM target_attempts
            );

            WITH target_attempts AS (
                SELECT
                    a.id
                FROM attempts a
                JOIN participants p
                    ON p.id = a.participant_id
                JOIN users u
                    ON u.id = p.user_id
                WHERE
                    a.exam_day_id = %s
                    AND CAST(
                        REPLACE(
                            u.firebase_uid,
                            'dev-user-',
                            ''
                        ) AS INTEGER
                    )
                    BETWEEN %s AND %s
            )

            DELETE FROM responses
            WHERE attempt_id IN (
                SELECT id FROM target_attempts
            );

            WITH target_attempts AS (
                SELECT
                    a.id
                FROM attempts a
                JOIN participants p
                    ON p.id = a.participant_id
                JOIN users u
                    ON u.id = p.user_id
                WHERE
                    a.exam_day_id = %s
                    AND CAST(
                        REPLACE(
                            u.firebase_uid,
                            'dev-user-',
                            ''
                        ) AS INTEGER
                    )
                    BETWEEN %s AND %s
            )

            DELETE FROM attempt_events
            WHERE attempt_id IN (
                SELECT id FROM target_attempts
            );

            WITH target_attempts AS (
                SELECT
                    a.id
                FROM attempts a
                JOIN participants p
                    ON p.id = a.participant_id
                JOIN users u
                    ON u.id = p.user_id
                WHERE
                    a.exam_day_id = %s
                    AND CAST(
                        REPLACE(
                            u.firebase_uid,
                            'dev-user-',
                            ''
                        ) AS INTEGER
                    )
                    BETWEEN %s AND %s
            )

            DELETE FROM attempts
            WHERE id IN (
                SELECT id FROM target_attempts
            );
            """

            cur.execute(
                delete_sql,
                (
                    args.exam_day,
                    args.start_user,
                    args.end_user,

                    args.exam_day,
                    args.start_user,
                    args.end_user,

                    args.exam_day,
                    args.start_user,
                    args.end_user,

                    args.exam_day,
                    args.start_user,
                    args.end_user,
                ),
            )

            conn.commit()

            print()
            print("Reset completed successfully.")

    except Exception as e:
        conn.rollback()
        print()
        print("ERROR")
        print(e)
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    main()