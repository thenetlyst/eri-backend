from sqlalchemy.orm import Session

from app.models.attempt import Attempt, AttemptStatus
from app.models.participant_progress import ParticipantProgress
from app.models.question import Question
from app.models.participant import Participant
from app.models.attempt_answer import AttemptAnswer

# =========================================================
# SINGLE PARTICIPANT REBUILD
# =========================================================
def rebuild_participant_progress(
    db: Session,
    participant_id,
    challenge_id,
):
    """
    Deterministically rebuild participant_progress from attempts.
    Safe to run multiple times (idempotent).
    Scales — uses exam_day question cache.
    """

    attempts = (
        db.query(Attempt)
        .filter(
            Attempt.participant_id == participant_id,
            Attempt.challenge_id == challenge_id,
            Attempt.status == AttemptStatus.SUBMITTED,
        )
        .order_by(Attempt.started_at)
        .all()
    )

    attendance_count = 0
    days_completed = 0
    cumulative_score = 0
    cumulative_base_effective_score = 0
    cumulative_base_max = 0

    # ⭐ Prevent N+1 queries
    exam_day_cache = {}

    for attempt in attempts:

        # ---------- QUESTION CACHE ----------
        if attempt.exam_day_id not in exam_day_cache:
            exam_day_cache[attempt.exam_day_id] = (
                db.query(Question)
                .filter(Question.exam_day_id == attempt.exam_day_id)
                .all()
            )

        questions = exam_day_cache[attempt.exam_day_id]

        base_questions = [q for q in questions if not q.is_special]

        base_max = sum(float(q.weight) for q in base_questions)
        base_score = float(attempt.raw_score)

        attendance_count += 1
        days_completed += 1

        cumulative_score += float(attempt.final_score)
        cumulative_base_effective_score += base_score
        cumulative_base_max += base_max

    # ---------- BONUS ELIGIBILITY ----------
    eligible_for_bonus_next_day = False

    if cumulative_base_max > 0:
        pct = cumulative_base_effective_score / cumulative_base_max
        eligible_for_bonus_next_day = (
            days_completed >= 2
            and pct >= 0.7
            and attendance_count == days_completed
        )

    # ---------- UPSERT PROGRESS ----------
    progress = (
        db.query(ParticipantProgress)
        .filter(
            ParticipantProgress.participant_id == participant_id,
            ParticipantProgress.challenge_id == challenge_id,
        )
        .first()
    )

    if not progress:
        progress = ParticipantProgress(
            participant_id=participant_id,
            challenge_id=challenge_id,
        )
        db.add(progress)

    progress.attendance_count = attendance_count
    progress.days_completed = days_completed
    progress.cumulative_score = cumulative_score
    progress.cumulative_base_effective_score = cumulative_base_effective_score
    progress.cumulative_base_max = cumulative_base_max
    progress.eligible_for_bonus_next_day = eligible_for_bonus_next_day

    db.commit()
    return progress


# =========================================================
# FULL CHALLENGE REBUILD
# =========================================================
def rebuild_challenge_progress(db: Session, challenge_id):
    """
    Rebuild progress for all participants in a challenge.
    Safe for large scale (batch friendly).
    """

    participants = (
        db.query(Participant.id)
        .filter(Participant.challenge_id == challenge_id)
        .all()
    )

    total = len(participants)
    rebuilt = 0

    for p in participants:
        rebuild_participant_progress(db, p.id, challenge_id)
        rebuilt += 1

        # ⭐ progress logging
        if rebuilt % 50 == 0:
            print(f"[REBUILD] {rebuilt}/{total}")

    return {
        "participants_found": total,
        "participants_rebuilt": rebuilt,
    }