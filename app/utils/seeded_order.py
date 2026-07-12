# app/utils/seeded_order.py

import random
from typing import List


def seeded_shuffle(ids: List[str], seed: str) -> List[str]:
    """
    Deterministic shuffle using attempt seed.
    Same ids + same seed → same order forever.
    """
    if not ids:
        return []

    rng = random.Random(seed)
    ordered = ids.copy()
    rng.shuffle(ordered)
    return ordered


def build_attempt_order(
    base_ids: List[str],
    bonus_ids: List[str],
    seed: str,
    special_unlocked: bool,
) -> List[str]:
    """
    Builds full navigation order for attempt.

    Base → shuffled
    Bonus → appended (not shuffled)
    """

    ordered_base = seeded_shuffle(base_ids, seed+ ":base")

    if special_unlocked and bonus_ids:
        return ordered_base + bonus_ids

    return ordered_base