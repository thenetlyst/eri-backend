from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Dict
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.exam_day import ExamDay
from app.models.challenge import Challenge, ChallengeStatus
from app.services.question_cache import get_exam_day_questions_cached


@dataclass(frozen=True)
class ExamRuntime:

    challenge_id: UUID

    day_number: int

    window_start: object

    window_end: object

    grace_seconds: int

    force_locked: bool

    question_map: dict

    base_ids: tuple[str, ...]

    bonus_ids: tuple[str, ...]

    total_questions: int

    base_question_count: int

    bonus_question_count: int

    total_allowed_seconds: int


class ExamRuntimeCache:

    def __init__(self):

        self._cache: Dict[UUID, ExamRuntime] = {}

        self._lock = Lock()

    def get(
        self,
        db: Session,
        exam_day_id: UUID,
    ) -> ExamRuntime:

        runtime = self._cache.get(exam_day_id)

        if runtime is not None:
            return runtime

        with self._lock:

            runtime = self._cache.get(exam_day_id)

            if runtime is not None:
                return runtime

            runtime = self._load(db, exam_day_id)

            self._cache[exam_day_id] = runtime

            return runtime

    def invalidate(
        self,
        exam_day_id: UUID,
    ):

        with self._lock:
            self._cache.pop(exam_day_id, None)

    def clear(self):

        with self._lock:
            self._cache.clear()

    def stats(self):

        return {
            "entries": len(self._cache),
        }

    def _load(
        self,
        db: Session,
        exam_day_id: UUID,
    ) -> ExamRuntime:

        exam_day = (
            db.query(ExamDay)
            .filter(ExamDay.id == exam_day_id)
            .first()
        )

        if exam_day is None:
            raise ValueError(f"Exam day {exam_day_id} not found")

        challenge = (
            db.query(Challenge)
            .filter(Challenge.id == exam_day.challenge_id)
            .first()
        )

        if challenge is None:
            raise ValueError(
                f"Challenge {exam_day.challenge_id} not found"
            )

        if challenge.status != ChallengeStatus.ACTIVE:
            raise ValueError("Challenge is not active")

        question_map = get_exam_day_questions_cached(
            str(exam_day.id)
        )

        questions = list(question_map.values())

        base_ids = tuple(
            sorted(
                q["id"]
                for q in questions
                if not q["is_special"]
            )
        )

        bonus_ids = tuple(
            sorted(
                q["id"]
                for q in questions
                if q["is_special"]
            )
        )

        total_allowed = sum(
            q["allocated_time_seconds"]
            for q in questions
            if not q["is_special"]
        )

        return ExamRuntime(

            challenge_id=challenge.id,

            day_number=exam_day.day_number,

            window_start=exam_day.window_start,

            window_end=exam_day.window_end,

            grace_seconds=exam_day.grace_seconds,

            force_locked=exam_day.is_force_locked,

            question_map=question_map,

            base_ids=base_ids,

            bonus_ids=bonus_ids,

            total_questions=len(questions),

            base_question_count=len(base_ids),

            bonus_question_count=len(bonus_ids),

            total_allowed_seconds=int(total_allowed),
        )


exam_runtime_cache = ExamRuntimeCache()