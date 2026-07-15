from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Dict
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings


# =======================================================
# Immutable Exam Context
# =======================================================
#
# This object contains ONLY immutable exam metadata.
#
# Never store:
#
# - SQLAlchemy ORM objects
# - Sessions
# - Participant data
# - Attempts
# - Responses
# - Progress
#
# Only immutable snapshots.
#
# =======================================================


@dataclass(frozen=True)
class ExamContext:
    exam_day: dict

    challenge: dict

    question_map: dict

    ordered_question_ids: tuple

    base_question_ids: tuple

    bonus_question_ids: tuple

    total_questions: int

    base_question_count: int

    bonus_question_count: int

    total_duration_seconds: int


# =======================================================
# Exam Context Cache
# =======================================================


class ExamContextCache:
    def __init__(self):
        self._cache: Dict[UUID, ExamContext] = {}
        self._lock = Lock()

    # --------------------------------------------------

    def get_exam_context(
        self,
        db: Session,
        exam_day_id: UUID,
    ) -> ExamContext:
        """
        Returns the immutable ExamContext.

        If caching is disabled, always loads directly
        from the database.

        Otherwise:

            Cache
                ↓
            Database (on miss)
        """

        if not settings.EXAM_CONTEXT_CACHE_ENABLED:
            return self._load_context(
                db,
                exam_day_id,
            )

        context = self._cache.get(exam_day_id)

        if context is not None:
            return context

        with self._lock:

            context = self._cache.get(exam_day_id)

            if context is not None:
                return context

            context = self._load_context(
                db,
                exam_day_id,
            )

            self._cache[exam_day_id] = context

            return context

    # --------------------------------------------------

    def warm_exam_context(
        self,
        db: Session,
        exam_day_id: UUID,
    ) -> None:
        """
        Pre-load an exam into cache.
        """

        self.get_exam_context(
            db,
            exam_day_id,
        )

    # --------------------------------------------------

    def invalidate_exam_context(
        self,
        exam_day_id: UUID,
    ) -> None:
        """
        Remove one exam from cache.
        """

        with self._lock:
            self._cache.pop(
                exam_day_id,
                None,
            )

    # --------------------------------------------------

    def clear(self) -> None:
        """
        Remove every cached exam.
        """

        with self._lock:
            self._cache.clear()

    # --------------------------------------------------

    def contains(
        self,
        exam_day_id: UUID,
    ) -> bool:
        """
        Returns True if exam exists in cache.
        """

        return exam_day_id in self._cache

    # --------------------------------------------------

    def stats(self) -> dict:
        """
        Cache diagnostics.
        """

        with self._lock:
            return {
                "enabled": settings.EXAM_CONTEXT_CACHE_ENABLED,
                "entries": len(self._cache),
            }

    # --------------------------------------------------
    # Phase 2
    # --------------------------------------------------

    def _load_context(
        self,
        db: Session,
        exam_day_id: UUID,
    ) -> ExamContext:
        """
        Build immutable ExamContext.

        IMPORTANT

        This method must NEVER cache SQLAlchemy ORM
        instances.

        It must return only immutable snapshots
        (dicts, tuples, dataclasses).

        Implemented in Phase 2.
        """

        raise NotImplementedError(
            "ExamContext loading will be implemented in Phase 2."
        )


# =======================================================
# Singleton
# =======================================================

exam_context_cache = ExamContextCache()