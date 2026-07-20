from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.models.exam_day import ExamDay
from app.models.challenge import Challenge
from app.models.participant import Participant
from app.models.participant_progress import ParticipantProgress


@dataclass(frozen=True)
class AttemptContext:
    exam_day: ExamDay
    challenge: Challenge
    participant: Participant
    progress: Optional[ParticipantProgress]
    now: datetime