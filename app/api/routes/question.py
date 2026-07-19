# app/api/routes/question.p
import random
import hashlib
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.attempt import Attempt, AttemptStatus
from app.models.attempt_answer import AttemptAnswer
from app.services.attempt_service import finalize_attempt
from app.services.question_cache import get_exam_day_questions_cached

from time import perf_counter
import logging
import threading
import os
from app.core.exceptions import (
    NotFoundException,
    ForbiddenException,
)


logger = logging.getLogger(__name__)

router = APIRouter(tags=["Questions"])


# ==========================================================
# LIST QUESTIONS (CACHED)
# ==========================================================
@router.get("/{attempt_id}/questions")
def list_questions(
    attempt_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    try:

        request_start = perf_counter()

        print("\n========================================")
        print("ENTER list_questions")
        print(f"PID       = {os.getpid()}")
        print(f"Thread    = {threading.get_ident()}")
        print(f"attempt_id = {attempt_id}")
        print("========================================")

        lookup_start = perf_counter()

        attempt = (
            db.query(Attempt)
            .options(joinedload(Attempt.participant))
            .filter(
                Attempt.id == attempt_id
            )
            .first()
        )

        print("✓ Attempt lookup complete")

        if attempt:
            print(f"status={attempt.status}")
            print(f"exam_day_id={attempt.exam_day_id}")
        else:
            print("Attempt NOT FOUND")

        logger.info(
            "LIST_QUESTIONS attempt_lookup_ms=%.2f",
            (perf_counter() - lookup_start) * 1000,
        )

        if not attempt:
            raise NotFoundException("Attempt not found")
    
        if attempt.participant.user_id != current_user.id:
            raise ForbiddenException("Unauthorized access to attempt")
    
        if attempt.status == AttemptStatus.SUBMITTED:
            raise ForbiddenException("Attempt already completed")

        # ⭐ CACHE HIT
        cache_start = perf_counter()

        cached_questions = get_exam_day_questions_cached(
            str(attempt.exam_day_id)
        )

        print(f"✓ Cache lookup complete ({len(cached_questions)} cached questions)")

        logger.info(
            "LIST_QUESTIONS cache_lookup_ms=%.2f",
            (perf_counter() - cache_start) * 1000,
        )

        # IMPORTANT → copy before use
        questions = [q.copy() for q in cached_questions.values()]

        answers_start = perf_counter()

        answers = (
            db.query(AttemptAnswer)
            .filter(
                AttemptAnswer.attempt_id == attempt.id
            )
            .all()
        )

        print(f"✓ Answers loaded ({len(answers)} answers)")

        logger.info(
            "LIST_QUESTIONS answers_query_ms=%.2f",
            (perf_counter() - answers_start) * 1000,
        )

        answered_map = {str(a.question_id): a for a in answers}

        build_start = perf_counter()

        result = []

        print("Building manifest...")

        total_base = sum(1 for x in questions if not x["is_special"])
        answered_base = sum(
            1
            for a in answers
            if not next(q2 for q2 in questions if q2["id"] == str(a.question_id))["is_special"]
        )

        for q in questions:
            qid = q["id"]

            is_answered = qid in answered_map

            bonus_locked = False
            if q["is_special"]:
                if not attempt.special_unlocked:
                    bonus_locked = True
                elif answered_base < total_base:
                    bonus_locked = True

            result.append(
                {
                    "question_id": qid,
                    "question_order": q["question_order"],
                    "difficulty": q["difficulty"],
                    "weight": q["weight"],
                    "is_special": q["is_special"],
                    "is_answered": is_answered,
                    "bonus_locked": bonus_locked,
                }
            )

        logger.info(
            "LIST_QUESTIONS build_manifest_ms=%.2f",
            (perf_counter() - build_start) * 1000,
        )

        logger.info(
            "LIST_QUESTIONS total_ms=%.2f",
            (perf_counter() - request_start) * 1000,
        )

        print(f"✓ Returning manifest ({len(result)} questions)")
        print("EXIT list_questions")
        print("========================================\n")

        return result
    except Exception as e:
        import traceback

        print("\nXXXXXXXX LIST_QUESTIONS EXCEPTION XXXXXXXX")
        print(e)
        traceback.print_exc()
        print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")

        raise

# ==========================================================
# FETCH SINGLE QUESTION (CACHED)
# ==========================================================
@router.get("/{attempt_id}/questions/{question_order}")
def get_question(
    attempt_id: str,
    question_order: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    now = datetime.now(timezone.utc)

    attempt = db.query(Attempt).filter(
        Attempt.id == attempt_id
    ).first()

    if not attempt:
        raise NotFoundException("Attempt not found")

    if attempt.participant.user_id != current_user.id:
        raise ForbiddenException("Unauthorized access to attempt")

    if attempt.status == AttemptStatus.SUBMITTED:
        raise ForbiddenException("Attempt already completed")

    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise ForbiddenException("Attempt is not active")

    if not attempt.started_at:
        raise ForbiddenException("Attempt not properly started")

    if attempt.allowed_duration_seconds is None:
        raise ForbiddenException("Attempt duration not configured")

    expiry_time = attempt.started_at + timedelta(
        seconds=attempt.allowed_duration_seconds
    )

    if now > expiry_time:
        finalize_attempt(db, attempt)
        db.commit()
        raise ForbiddenException("Attempt time expired")

    remaining_time = int((expiry_time - now).total_seconds())

    # ⭐ CACHE HIT
    cached_questions = get_exam_day_questions_cached(str(attempt.exam_day_id))
    questions = [q.copy() for q in cached_questions.values()]

    question = next(
        (q for q in questions if q["question_order"] == question_order),
        None
    )

    if not question:
        raise NotFoundException("Question not found")

    # Bonus gating
    if question["is_special"]:
        if not attempt.special_unlocked:
            raise ForbiddenException("Bonus not unlocked")

        total_base = sum(1 for x in questions if not x["is_special"])

        answers = db.query(AttemptAnswer).filter(
            AttemptAnswer.attempt_id == attempt.id
        ).all()

        answered_base = sum(
            1
            for a in answers
            if not next(q2 for q2 in questions if q2["id"] == str(a.question_id))["is_special"]
        )

        if answered_base < total_base:
            raise ForbiddenException("Complete base section before accessing bonus")

    existing_answer = db.query(AttemptAnswer).filter(
        AttemptAnswer.attempt_id == attempt.id,
        AttemptAnswer.question_id == question["id"],
    ).first()

    is_answered = existing_answer is not None
    hint_used = existing_answer.hint_used if existing_answer else False

    # ⭐ JSON content (new)
    content = question.get("content_json")

    # Fallback options (legacy)
    options = [
        {"key": "A", "text": question["option_a"]},
        {"key": "B", "text": question["option_b"]},
        {"key": "C", "text": question["option_c"]},
        {"key": "D", "text": question["option_d"]},
    ]

    seed_input = f"{attempt.id}-{question['id']}"
    seed_hash = hashlib.sha256(seed_input.encode()).hexdigest()
    seed = int(seed_hash, 16)

    rng = random.Random(seed)
    rng.shuffle(options)

    return {
        "question_id": question["id"],
        "question_order": question["question_order"],

        # ⭐ NEW JSON content
        "content": content,

        # fallback legacy fields
        "question_text": question["question_text"],

        "difficulty": question["difficulty"],
        "weight": question["weight"],
        "hint_penalty_percentage": question["hint_penalty_percentage"],
        "is_special": question["is_special"],
        "is_answered": is_answered,
        "hint_used": hint_used,
        "options": options,
        "remaining_time_seconds": max(remaining_time, 0),
    }
# ==========================================================
# DEBUG — CLEAR QUESTION CACHE (REMOVE LATER)
# ==========================================================
@router.post("/debug/clear-question-cache")
def clear_question_cache():
    from app.services.question_cache import get_exam_day_questions_cached

    get_exam_day_questions_cached.cache_clear()

    return {"status": "question cache cleared"}
