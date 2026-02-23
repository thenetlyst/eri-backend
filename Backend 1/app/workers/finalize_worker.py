import asyncio
from datetime import datetime, timezone, timedelta

from app.db.session import SessionLocal
from app.models.attempt import Attempt, AttemptStatus
from app.services.attempt_service import finalize_attempt


SWEEP_INTERVAL_SECONDS = 45
BATCH_SIZE = 50


async def finalize_expired_attempts_loop():
    print("[FinalizeWorker] Loop started")

    while True:
        db = SessionLocal()

        try:
            active_attempts = (
                db.query(Attempt)
                .filter(Attempt.status == AttemptStatus.IN_PROGRESS)
                .limit(BATCH_SIZE)
                .all()
            )

            now = datetime.now(timezone.utc)
            to_finalize = []

            for attempt in active_attempts:
                expiry = attempt.started_at + timedelta(
                    seconds=attempt.allowed_duration_seconds
                )

                if now >= expiry:
                    to_finalize.append(attempt)

            if to_finalize:
                print(f"[FinalizeWorker] Finalizing {len(to_finalize)} attempts")

            for attempt in to_finalize:
                try:
                    finalize_attempt(db, attempt)

                    db.flush()
                    db.expire_all()
                    db.commit()

                except Exception as e:
                    db.rollback()
                    print("[FinalizeWorker] Failed attempt:", attempt.id, e)

        except Exception as e:
            db.rollback()
            print("[FinalizeWorker] Error:", e)

        finally:
            db.close()

        await asyncio.sleep(SWEEP_INTERVAL_SECONDS)