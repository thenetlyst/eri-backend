from datetime import datetime, timezone
import hashlib
import random

from app.utils.seeded_order import build_attempt_order


# ==========================================================
# 🔒 OPTION SHUFFLER (SAFE + DETERMINISTIC)
# ==========================================================
def build_shuffled_options(attempt_id, question, raw_options=None):
    """
    Builds deterministic shuffled options with stable IDs.

    - Preserves original keys (A/B/C/D)
    - Adds option_id for frontend usage
    - Works with both DB options and content_json options
    """

    if raw_options:
        options = [
            {
                "id": f"{question.id}_{opt.get('key')}",
                "key": opt.get("key"),
                "text": opt.get("text"),
                "image_url": opt.get("image_url"), # ADD This
            }
            for opt in raw_options
        ]
    else:
        options = [
            {"id": f"{question.id}_A", "key": "A", "text": question.option_a},
            {"id": f"{question.id}_B", "key": "B", "text": question.option_b},
            {"id": f"{question.id}_C", "key": "C", "text": question.option_c},
            {"id": f"{question.id}_D", "key": "D", "text": question.option_d},
        ]

    # 🔒 deterministic per attempt + question
    seed_input = f"{attempt_id}-{question.id}"
    seed_hash = hashlib.sha256(seed_input.encode()).hexdigest()
    seed = int(seed_hash, 16)

    rng = random.Random(seed)
    rng.shuffle(options)

    return options


# ==========================================================
# 📦 SNAPSHOT BUILDER
# ==========================================================
def build_attempt_snapshot(attempt, questions, answers):
    """
    Compose authoritative attempt snapshot.
    Pure read — no writes.
    """

    now = datetime.now(timezone.utc)

    # ==========================================================
    # ⏱ TIMING (DISPLAY ONLY)
    # ==========================================================
    actual_elapsed = int((now - attempt.started_at).total_seconds())

    elapsed = min(
        actual_elapsed,
        attempt.allowed_duration_seconds
    )

    remaining = max(
        attempt.allowed_duration_seconds - elapsed,
        0
    )

    # ==========================================================
    # 🧠 ANSWER MAP
    # ==========================================================
    answer_map = {}
    for a in answers:
        answer_map[str(a.question_id)] = {
            "selected_option": a.selected_option,
            "marked_for_review": a.marked_for_review,
            "hint_used": a.hint_used,
            "answer_change_count": a.answer_change_count,
            "time_to_first_hint_seconds": a.time_to_first_hint_seconds,
        }

    # ==========================================================
    # 🔢 DETERMINISTIC QUESTION ORDER (SINGLE SOURCE OF TRUTH)
    # ==========================================================
    pool = attempt.question_pool_ids or {}

    base_ids = pool.get("base", [])
    bonus_ids = pool.get("bonus", [])

    final_order_ids = build_attempt_order(
        base_ids=base_ids,
        bonus_ids=bonus_ids,
        seed=attempt.shuffle_seed,
        special_unlocked=attempt.special_unlocked,
    )

    # ==========================================================
    # 🗺 MAP QUESTIONS
    # ==========================================================
    question_map = {str(q.id): q for q in questions}

    ordered_questions = [
        question_map[qid]
        for qid in final_order_ids
        if qid in question_map
    ]

    # ==========================================================
    # 🧱 BUILD QUESTION ITEMS
    # ==========================================================
    question_items = []

    for index, q in enumerate(ordered_questions, start=1):
        ans = answer_map.get(str(q.id))

        # -----------------------------
        # CONTENT
        # -----------------------------
        if q.content_json and isinstance(q.content_json, dict):
            content = q.content_json.get("content", q.question_text)
            image_url = q.content_json.get("image_url")

            raw_options = q.content_json.get("options")

            options = build_shuffled_options(
                attempt.id,
                q,
                raw_options=raw_options
            )
        else:
            content = q.question_text
            image_url = None

            options = build_shuffled_options(
                attempt.id,
                q
            )

        # -----------------------------
        # FINAL QUESTION OBJECT
        # -----------------------------
        question_items.append(
            {
                "question_id": str(q.id),
                "display_index": index,
                "is_special": q.is_special,

                # CONTENT
                "content": content,
                "image_url": image_url,
                "options": options,

                # STATE
                "selected_option": ans["selected_option"] if ans else None,
                "marked_for_review": ans["marked_for_review"] if ans else False,

                # HINT
                "hint": {
                    "used": ans["hint_used"] if ans else False,
                    "time_to_first_hint": (
                        ans["time_to_first_hint_seconds"] if ans else None
                    ),
                    "text": (
                        q.content_json.get("hint_text")
                        if q.content_json
                        and isinstance(q.content_json, dict)
                        and q.content_json.get("hint_text")
                        else q.hint_text
                    ),
                },

                "answer_change_count": (
                    ans["answer_change_count"] if ans else 0
                ),
            }
        )

    # ==========================================================
    # 📦 FINAL SNAPSHOT
    # ==========================================================
    snapshot = {
        "attempt": {
            "id": str(attempt.id),
            "state": attempt.status.value,
            "current_index": attempt.current_index,
            "special_unlocked": attempt.special_unlocked,
            "started_at": attempt.started_at.isoformat()
            if attempt.started_at
            else None,
            "allowed_duration_seconds": attempt.allowed_duration_seconds,
        },
        "timing": {
            "elapsed_seconds": int(elapsed),
            "remaining_seconds": remaining,
        },
        "questions": question_items,
        "answers": answer_map,
    }

    return snapshot