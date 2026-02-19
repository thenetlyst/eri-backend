# app/services/question_cache.py

from functools import lru_cache
from typing import List, Dict

from app.db.session import SessionLocal
from app.models.question import Question


@lru_cache(maxsize=200)
def get_exam_day_questions_cached(exam_day_id: str) -> List[Dict]:
    """
    Returns immutable-friendly question metadata cached in memory.
    Questions are static during exam window.
    """

    print("🔥 DB HIT → loading questions")

    db = SessionLocal()

    try:
        questions = (
            db.query(Question)
            .filter(Question.exam_day_id == exam_day_id)
            .order_by(Question.question_order)
            .all()
        )

        serialized: List[Dict] = []

        for q in questions:
            serialized.append(
                {
                    "id": str(q.id),
                    "question_order": q.question_order,
                    "difficulty": q.difficulty,
                    "weight": float(q.weight),
                    "is_special": q.is_special,
                    "question_text": q.question_text,
                    "option_a": q.option_a,
                    "option_b": q.option_b,
                    "option_c": q.option_c,
                    "option_d": q.option_d,
                    "hint_penalty_percentage": float(q.hint_penalty_percentage),
                }
            )

        return serialized

    finally:
        db.close()
