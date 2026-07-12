import asyncio
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy import func
import logging

from app.db.session import SessionLocal
from app.models.attempt import Attempt, AttemptStatus
from app.services.attempt_service import finalize_attempt

logger = logging.getLogger(__name__)

SWEEP_INTERVAL_SECONDS = 90
BATCH_SIZE = 5  # keep small for low lock pressure

AUTO_FINALIZE_ENABLED = os.getenv("AUTO_FINALIZE_ENABLED", "true").lower() == "true"


async def finalize_expired_attempts_loop():
    print("\n================ WORKER STARTED ================\n", flush=True)

    retry_delay = 1

    while True:
        try:
            now = datetime.now(timezone.utc)

            print(f"\n===== WORKER TICK {now.isoformat()} =====", flush=True)

            total_finalized = 0

            while True:
                db = SessionLocal()

                try:
                    attempts_to_finalize = []

                    print("Checking manual submissions...", flush=True)

                    submitted_attempts = (
                        db.query(Attempt)
                        .filter(
                            Attempt.status == AttemptStatus.SUBMITTED,
                            Attempt.progress_applied == False,
                            Attempt.submitted_at.isnot(None),
                            Attempt.submitted_at < now - timedelta(seconds=15),
                        )
                        .order_by(Attempt.started_at)
                        .with_for_update(skip_locked=True)
                        .limit(BATCH_SIZE)
                        .all()
                    )

                    print(
                        f"Manual submissions found: {len(submitted_attempts)}",
                        flush=True,
                    )

                    attempts_to_finalize.extend(submitted_attempts)

                    if AUTO_FINALIZE_ENABLED:
                        print("Checking expired attempts...", flush=True)

                        expired_attempts = (
                            db.query(Attempt)
                            .filter(
                                Attempt.status == AttemptStatus.IN_PROGRESS,
                                Attempt.started_at.isnot(None),
                                Attempt.allowed_duration_seconds.isnot(None),
                                func.extract(
                                    "epoch",
                                    now - Attempt.started_at,
                                )
                                >= Attempt.allowed_duration_seconds,
                            )
                            .order_by(Attempt.started_at)
                            .with_for_update(skip_locked=True)
                            .limit(BATCH_SIZE)
                            .all()
                        )

                        print(
                            f"Expired attempts found: {len(expired_attempts)}",
                            flush=True,
                        )

                        attempts_to_finalize.extend(expired_attempts)

                    seen = set()
                    unique_attempts = []

                    for attempt in attempts_to_finalize:
                        if attempt.id not in seen:
                            seen.add(attempt.id)
                            unique_attempts.append(attempt)

                    attempts_to_finalize = unique_attempts

                    print(
                        f"Unique attempts to finalize: {len(attempts_to_finalize)}",
                        flush=True,
                    )

                    if not attempts_to_finalize:
                        print("No attempts found in this batch.", flush=True)
                        break

                    for attempt in attempts_to_finalize:

                        print(
                            f"\nProcessing attempt: {attempt.id}",
                            flush=True,
                        )

                        try:
                            print("Calling finalize_attempt()", flush=True)

                            finalize_attempt(db, attempt)

                            print("Returned from finalize_attempt()", flush=True)

                            total_finalized += 1

                        except Exception:
                            print(
                                "\nEXCEPTION INSIDE finalize_attempt()\n",
                                flush=True,
                            )
                            import traceback

                            traceback.print_exc()

                    print("Calling db.commit()", flush=True)

                    db.commit()

                    print("Commit successful", flush=True)

                    await asyncio.sleep(0.1)

                except Exception:
                    print("\nBATCH FAILURE\n", flush=True)

                    import traceback

                    traceback.print_exc()

                    db.rollback()

                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 30)

                    break

                finally:
                    db.close()

            print(
                f"\nCycle complete. Finalized: {total_finalized}\n",
                flush=True,
            )

            retry_delay = 1

            await asyncio.sleep(1)

        except Exception:
            print("\nFATAL LOOP FAILURE\n", flush=True)

            import traceback

            traceback.print_exc()

            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 30)

        print(
            f"Sleeping {SWEEP_INTERVAL_SECONDS} seconds...\n",
            flush=True,
        )

        await asyncio.sleep(SWEEP_INTERVAL_SECONDS)