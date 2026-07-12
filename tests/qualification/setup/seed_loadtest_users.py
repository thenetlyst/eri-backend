#!/usr/bin/env python3

import argparse
import uuid

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import User
from app.models.participant import (
    Participant,
    AccountStatus,
)


DEFAULT_STATE = "Tamil Nadu"
DEFAULT_COLLEGE = "Load Test College"
DEFAULT_GRAD_YEAR = "2027"


def seed_users(start, count, challenge_id):

    db = SessionLocal()

    created_users = 0
    existing_users = 0

    created_participants = 0
    existing_participants = 0

    try:

        challenge_uuid = uuid.UUID(challenge_id)

        new_users = []

        # ----------------------------------------
        # Create Users
        # ----------------------------------------

        for i in range(start, start + count):

            email = f"loadtest_user_{i}@test.com"

            user = (
                db.query(User)
                .filter(User.email == email)
                .first()
            )

            if user is None:

                user = User(
                    email=email,
                    name=f"Load Test User {i}",
                    firebase_uid=f"dev-user-{i}",
                    participant_code=f"LT{i:06d}",
                )

                db.add(user)

                new_users.append(user)

                created_users += 1

            else:

                existing_users += 1

        db.flush()

        # ----------------------------------------
        # Create Participants
        # ----------------------------------------

        for i in range(start, start + count):

            email = f"loadtest_user_{i}@test.com"

            user = (
                db.query(User)
                .filter(User.email == email)
                .first()
            )

            participant = (
                db.query(Participant)
                .filter(
                    Participant.user_id == user.id,
                    Participant.challenge_id == challenge_uuid,
                )
                .first()
            )

            if participant is not None:

                existing_participants += 1
                continue

            participant = Participant(
                user_id=user.id,
                challenge_id=challenge_uuid,
                name=user.name,
                college=DEFAULT_COLLEGE,
                state=DEFAULT_STATE,
                graduation_year=DEFAULT_GRAD_YEAR,
                account_status=AccountStatus.ACTIVE,
            )

            db.add(participant)

            created_participants += 1

        db.commit()

        print()
        print("====================================")
        print("Load Test Seeder Complete")
        print("====================================")
        print(f"Created Users         : {created_users}")
        print(f"Existing Users        : {existing_users}")
        print(f"Created Participants  : {created_participants}")
        print(f"Existing Participants : {existing_participants}")
        print("====================================")

    except Exception:

        db.rollback()
        raise

    finally:

        db.close()


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--start",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--count",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--challenge-id",
        required=True,
    )

    args = parser.parse_args()

    seed_users(
        start=args.start,
        count=args.count,
        challenge_id=args.challenge_id,
    )


if __name__ == "__main__":
    main()