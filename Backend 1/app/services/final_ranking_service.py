from decimal import Decimal, getcontext
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.attempt import Attempt, AttemptStatus
from app.models.attempt_answer import AttemptAnswer
from app.models.question import Question
from app.models.exam_day import ExamDay
from app.models.participant import Participant

from app.services.ranking_service import compute_day_score

getcontext().prec = 12


def compute_participant_final_score(
    db: Session,
    participant_id: str,
    challenge_id: str,
):
    """
    Computes ERI_total_score for one participant across all exam days.
    """

    exam_days = db.query(ExamDay).filter(
        ExamDay.challenge_id == challenge_id
    ).all()

    total_score = Decimal("0")
    total_hints_used = 0
    missed_days = 0

    for day in exam_days:

        result = compute_day_score(
            db,
            participant_id,
            day.id
        )

        total_score += result["final_day_score"]

        if result["missed_flag"]:
            missed_days += 1

    # Total hints used across challenge
    total_hints_used = db.query(
        func.coalesce(func.sum(Attempt.hints_used_count), 0)
    ).filter(
        Attempt.participant_id == participant_id,
        Attempt.challenge_id == challenge_id,
        Attempt.status == AttemptStatus.SUBMITTED
    ).scalar()

    total_hints_used = int(total_hints_used or 0)

    return {
        "ERI_total_score": total_score,
        "total_hints_used": total_hints_used,
        "missed_days": missed_days,
    }


def compute_full_challenge_ranking(
    db: Session,
    challenge_id: str,
):
    """
    Computes ranking for all participants in a challenge.
    Returns ordered list with strict unique rank.
    """

    participants = db.query(Participant).filter(
        Participant.challenge_id == challenge_id
    ).all()

    ranking_results = []

    for participant in participants:

        metrics = compute_participant_final_score(
            db,
            participant.id,
            challenge_id
        )

        ranking_results.append({
            "participant_id": participant.id,
            "ERI_total_score": metrics["ERI_total_score"],
            "total_hints_used": metrics["total_hints_used"],
            "missed_days": metrics["missed_days"],
        })

    # Strict unique ranking — Option B ordering
    ranking_results.sort(
        key=lambda x: (
            -x["ERI_total_score"],
            x["total_hints_used"],
            x["missed_days"],
            str(x["participant_id"])
        )
    )

    # Assign strict rank
    for index, row in enumerate(ranking_results, start=1):
        row["rank"] = index

    return ranking_results
