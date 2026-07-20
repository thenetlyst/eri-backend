from sqlalchemy.orm import Session

from app.services.attempt.context import AttemptContext


class AttemptReader:

    @staticmethod
    def load(
        db: Session,
        *,
        current_user,
        exam_day_id: int,
    ) -> AttemptContext:
        """
        Temporary stub.

        The existing start_attempt logic will be migrated here
        without changing behaviour.
        """
        raise NotImplementedError