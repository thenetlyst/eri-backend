from datetime import datetime, timezone


def build_attempt_snapshot(attempt, questions, answers):
    """
    Compose authoritative attempt snapshot.
    Pure read — no writes.
    """

    now = datetime.now(timezone.utc)

    elapsed = (now - attempt.started_at).total_seconds()
    remaining = max(0, attempt.allowed_duration_seconds - elapsed)

    answer_map = {a.question_id: a for a in answers}

    question_items = []

    for q in questions:
        ans = answer_map.get(q.id)

        question_items.append(
            {
                "question_id": q.id,
                "display_index": q.question_order,
                "is_special": q.is_special,
                "selected_option": ans.selected_option if ans else None,
                "marked_for_review": ans.marked_for_review if ans else False,
                "hint": {
                    "used": ans.hint_used if ans else False,
                    "opens": ans.hint_open_count if ans else 0,
                    "time_to_first_hint": (
                        ans.time_to_first_hint_seconds if ans else None
                    ),
                },
            }
        )

    snapshot = {
        "attempt": {
            "id": attempt.id,
            "state": attempt.status,
            "current_index": attempt.current_index,
            "special_unlocked": attempt.special_unlocked,
        },
        "timing": {
            "elapsed_seconds": elapsed,
            "remaining_seconds": remaining,
        },
        "questions": question_items,
    }

    return snapshot