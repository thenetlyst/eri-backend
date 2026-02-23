from app.models.attempt_event import AttemptEvent

EVENT_QUESTION_VIEWED = "QUESTION_VIEWED"
EVENT_ANSWER_CHANGED = "ANSWER_CHANGED"
EVENT_HINT_USED = "HINT_USED"


def log_attempt_event(db, attempt_id, question_id, event_type, client_ts=None):
    ev = AttemptEvent(
        attempt_id=attempt_id,
        question_id=question_id,
        event_type=event_type,
        client_ts=client_ts,
    )
    db.add(ev)
    db.commit()
    