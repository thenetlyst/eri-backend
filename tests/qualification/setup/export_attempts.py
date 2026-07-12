#!/usr/bin/env python3

import json

from pathlib import Path

from app.db.session import SessionLocal
from app.models.user import User
from app.models.participant import Participant
from app.models.attempt import Attempt, AttemptStatus


OUTPUT_FILE = Path("tests/qualification/data/attempts.json")


def export_attempts():

    db = SessionLocal()

    try:

        rows = (
            db.query(
                User.firebase_uid,
                Attempt.id,
                Attempt.question_pool_ids,
            )
            .select_from(User)
            .join(
                Participant,
                Participant.user_id == User.id,
            )
            .join(
                Attempt,
                Attempt.participant_id == Participant.id,
            )
            .filter(
                Attempt.status == AttemptStatus.IN_PROGRESS
            )
            .all()
        )

        output = []

        prefix = "dev-user-"

        for firebase_uid, attempt_id, pool in rows:

            if not firebase_uid:
                continue

            if not firebase_uid.startswith(prefix):
                continue

            pool = pool or {}

            base_questions = pool.get("base", [])

            if not base_questions:
                continue

            output.append(
                {
                    "user": int(firebase_uid[len(prefix):]),
                    "attempt_id": str(attempt_id),
                    "question_id": base_questions[0],
                }
            )

        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(
            OUTPUT_FILE,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(output, f, indent=4)

        print()
        print("====================================")
        print("Attempt Export Complete")
        print("====================================")
        print(f"Exported Attempts : {len(output)}")
        print(f"Output File       : {OUTPUT_FILE}")
        print("====================================")

    finally:
        db.close()


if __name__ == "__main__":
    export_attempts()