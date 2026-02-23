from datetime import datetime, timezone


def build_attempt_snapshot(attempt, questions, answers):
    """
    Compose authoritative attempt snapshot.
    Pure read — no writes.
    """

    now = datetime.now(timezone.utc)

    elapsed = (now - attempt.started_at).total_seconds()
    remaining = max(0, int(attempt.allowed_duration_seconds - elapsed))

    # Build JSON answer map
    answer_map = {}
    for a in answers:
        answer_map[str(a.question_id)] = {
            "selected_option": a.selected_option,
            "marked_for_review": a.marked_for_review,
            "hint_used": a.hint_used,
            "hint_open_count": a.hint_open_count,
            "time_to_first_hint_seconds": a.time_to_first_hint_seconds,
        }

    question_items = []

    for q in questions:
        ans = answer_map.get(str(q.id))

        question_items.append(
            {
                "question_id": str(q.id),
                "display_index": q.question_order,
                "is_special": q.is_special,
                "selected_option": ans["selected_option"] if ans else None,
                "marked_for_review": ans["marked_for_review"] if ans else False,
                "hint": {
                    "used": ans["hint_used"] if ans else False,
                    "opens": ans["hint_open_count"] if ans else 0,
                    "time_to_first_hint": (
                        ans["time_to_first_hint_seconds"] if ans else None
                    ),
                },
            }
        )

    snapshot = {
        "attempt": {
            "id": str(attempt.id),
            "state": attempt.status.value,   # ⭐ important
            "current_index": attempt.current_index,
            "special_unlocked": attempt.special_unlocked,
        },
        "timing": {
            "elapsed_seconds": int(elapsed),
            "remaining_seconds": remaining,
        },
        "questions": question_items,
        "answers": answer_map,  # ⭐ missing before
    }

    return snapshot