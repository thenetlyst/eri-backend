from functools import lru_cache
from typing import Dict
from threading import Lock

from app.db.session import SessionLocal
from app.models.question import Question

_cache_lock = Lock()


@lru_cache(maxsize=200)
def get_exam_day_questions_map(exam_day_id: str) -> Dict[str, dict]:
    """
    Returns:
    { question_id: question_data }
    """

    with _cache_lock:

        print("🔥 DB HIT → loading questions")

        db = SessionLocal()

        try:
            questions = (
                db.query(Question)
                .filter(Question.exam_day_id == exam_day_id)
                .order_by(Question.question_order)
                .all()
            )

            question_map = {}

            for q in questions:
                question_map[str(q.id)] = {
                    "id": str(q.id),
                    "question_order": q.question_order,
                    "difficulty": q.difficulty,
                    "weight": float(q.weight),
                    "is_special": q.is_special,
                    "allocated_time_seconds": q.allocated_time_seconds,
                    "question_text": q.question_text,
                    "option_a": q.option_a,
                    "option_b": q.option_b,
                    "option_c": q.option_c,
                    "option_d": q.option_d,
                    "correct_option": q.correct_option,
                    "hint_penalty_percentage": float(q.hint_penalty_percentage),
                    "content_json": q.content_json,
                }

            return question_map

        finally:
            db.close()


# ✅ BACKWARD COMPATIBILITY FIX
def get_exam_day_questions_cached(exam_day_id: str) -> Dict[str, dict]:
    """
    Wrapper to maintain compatibility with existing imports.
    DO NOT REMOVE.
    """
    return get_exam_day_questions_map(exam_day_id)