from sqlalchemy.orm import Session


class ExamSessionService:
    """
    Coordinates the exam lifecycle.

    This service intentionally contains almost no business logic.
    Existing logic is delegated to existing repositories/services.
    """

    @staticmethod
    def prepare(
        db: Session,
        *,
        exam_day_id,
        current_user,
        client_ip,
        user_agent,
    ):
        raise NotImplementedError

    @staticmethod
    def activate(
        db: Session,
        *,
        attempt,
    ):
        raise NotImplementedError