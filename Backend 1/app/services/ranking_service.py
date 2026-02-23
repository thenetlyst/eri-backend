from decimal import Decimal, getcontext
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.attempt import Attempt, AttemptStatus
from app.models.attempt_answer import AttemptAnswer
from app.models.question import Question

# High precision for ranking
getcontext().prec = 12

BONUS_WEIGHT_FACTOR = Decimal("0.30")


def compute_day_score(
    db: Session,
    participant_id: str,
    exam_day_id: str,
):
    """
    Computes the final_day_score for one participant on one exam day.

    Returns:
        {
            "base_effective_score": Decimal,
            "base_max_score": Decimal,
            "bonus_effective_score": Decimal,
            "core_normalized": Decimal,
            "bonus_boost": Decimal,
            "final_day_score": Decimal,
            "missed_flag": bool
        }
    """

    # -------------------------------------------------
    # 1️⃣ Fetch Attempt
    # -------------------------------------------------
    attempt = db.query(Attempt).filter(
        Attempt.participant_id == participant_id,
        Attempt.exam_day_id == exam_day_id,
    ).first()

    # Missed if no attempt or not submitted
    if not attempt or attempt.status != AttemptStatus.SUBMITTED:
        return {
            "base_effective_score": Decimal("0"),
            "base_max_score": Decimal("0"),
            "bonus_effective_score": Decimal("0"),
            "core_normalized": Decimal("0"),
            "bonus_boost": Decimal("0"),
            "final_day_score": Decimal("0"),
            "missed_flag": True,
        }

    # -------------------------------------------------
    # 2️⃣ Base Max Score
    # -------------------------------------------------
    base_max_score = db.query(
        func.coalesce(func.sum(Question.weight), 0)
    ).filter(
        Question.exam_day_id == exam_day_id,
        Question.is_special == False
    ).scalar()

    base_max_score = Decimal(base_max_score)

    if base_max_score == 0:
        # Defensive guard
        return {
            "base_effective_score": Decimal("0"),
            "base_max_score": Decimal("0"),
            "bonus_effective_score": Decimal("0"),
            "core_normalized": Decimal("0"),
            "bonus_boost": Decimal("0"),
            "final_day_score": Decimal("0"),
            "missed_flag": True,
        }

    # -------------------------------------------------
    # 3️⃣ Base Effective Score
    # -------------------------------------------------
    base_effective_score = db.query(
        func.coalesce(func.sum(AttemptAnswer.effective_score), 0)
    ).join(
        Question,
        AttemptAnswer.question_id == Question.id
    ).filter(
        AttemptAnswer.attempt_id == attempt.id,
        Question.is_special == False
    ).scalar()

    base_effective_score = Decimal(base_effective_score)

    # -------------------------------------------------
    # 4️⃣ Bonus Effective Score
    # -------------------------------------------------
    bonus_effective_score = db.query(
        func.coalesce(func.sum(AttemptAnswer.effective_score), 0)
    ).join(
        Question,
        AttemptAnswer.question_id == Question.id
    ).filter(
        AttemptAnswer.attempt_id == attempt.id,
        Question.is_special == True
    ).scalar()

    bonus_effective_score = Decimal(bonus_effective_score)

    # -------------------------------------------------
    # 5️⃣ Core Normalized
    # -------------------------------------------------
    core_normalized = base_effective_score / base_max_score

    # -------------------------------------------------
    # 6️⃣ Bonus Boost (Additive Only)
    # -------------------------------------------------
    bonus_boost = (
        (bonus_effective_score / base_max_score)
        * BONUS_WEIGHT_FACTOR
    )

    # -------------------------------------------------
    # 7️⃣ Final Day Score
    # -------------------------------------------------
    final_day_score = core_normalized + bonus_boost

    return {
        "base_effective_score": base_effective_score,
        "base_max_score": base_max_score,
        "bonus_effective_score": bonus_effective_score,
        "core_normalized": core_normalized,
        "bonus_boost": bonus_boost,
        "final_day_score": final_day_score,
        "missed_flag": False,
    }
