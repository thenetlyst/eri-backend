from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from collections import defaultdict
from decimal import Decimal, getcontext

from app.api.deps import get_db
from app.models.participant import Participant
from app.models.attempt import Attempt, AttemptStatus
from app.models.exam_day import ExamDay
from app.models.ranking import Ranking
from app.models.challenge import Challenge, ChallengeStatus
from app.core.config import settings
from app.core.exceptions import ForbiddenException, NotFoundException

router = APIRouter(prefix="/ranking", tags=["Ranking"])

getcontext().prec = 12


# ==========================================================
# LIVE COMPUTATION (NON-PERSISTENT)
# ==========================================================

@router.get("/challenge/{challenge_id}")
def compute_challenge_ranking(challenge_id: str, db: Session = Depends(get_db)):

    participants = db.query(Participant).filter(
        Participant.challenge_id == challenge_id
    ).all()

    if not participants:
        return {
            "total_participants": 0,
            "ranked_participants": 0,
            "top_10": []
        }

    attempts = db.query(Attempt).filter(
        Attempt.challenge_id == challenge_id,
        Attempt.status == AttemptStatus.SUBMITTED
    ).all()

    performance = defaultdict(lambda: {
        "total_score": Decimal("0"),
        "submitted_days": 0,
        "total_hints_used": 0
    })

    for attempt in attempts:
        pid = attempt.participant_id
        performance[pid]["total_score"] += Decimal(attempt.final_score or 0)
        performance[pid]["submitted_days"] += 1
        performance[pid]["total_hints_used"] += attempt.hints_used_count

    ranked_list = []

    for participant in participants:
        pid = participant.id
        data = performance.get(pid)

        if not data or data["submitted_days"] == 0:
            continue

        ranked_list.append({
            "participant_id": pid,
            "total_score": data["total_score"],
            "submitted_days": data["submitted_days"],
            "total_hints_used": data["total_hints_used"],
        })

    ranked_list.sort(
        key=lambda x: (
            -x["total_score"],
            -x["submitted_days"],
            x["total_hints_used"],
            str(x["participant_id"])
        )
    )

    for index, participant in enumerate(ranked_list):
        participant["rank"] = index + 1

    return {
        "total_participants": len(participants),
        "ranked_participants": len(ranked_list),
        "top_10": [
            {
                "participant_id": str(p["participant_id"]),
                "total_score": float(p["total_score"]),
                "rank": p["rank"]
            }
            for p in ranked_list[:10]
        ]
    }


# ==========================================================
# FINALIZE & PERSIST (GLOBAL + STATE RANKS)
# ==========================================================

@router.post("/finalize/{challenge_id}")
def finalize_challenge_ranking(
    challenge_id: str,
    force: bool = Query(False),
    admin_key: str | None = Query(None),
    db: Session = Depends(get_db)
):

    # 1️⃣ Validate Challenge
    challenge = db.query(Challenge).filter(
        Challenge.id == challenge_id
    ).first()

    if not challenge:
        raise NotFoundException("Challenge not found")

    # 2️⃣ Status Gate
    if challenge.status != ChallengeStatus.SCORING:

        if not force:
            raise ForbiddenException(
                "Ranking can only be finalized when challenge status is SCORING"
            )

        if not settings.RANKING_ADMIN_KEY:
            raise ForbiddenException("Admin override not configured")

        if admin_key != settings.RANKING_ADMIN_KEY:
            raise ForbiddenException("Invalid admin key for force override")

    # 3️⃣ Prevent Re-finalization
    existing = db.query(Ranking).filter(
        Ranking.challenge_id == challenge_id
    ).first()

    if existing and not force:
        raise ForbiddenException(
            "Ranking already finalized. Use force=true with admin_key."
        )

    participants = db.query(Participant).filter(
        Participant.challenge_id == challenge_id
    ).all()

    attempts = db.query(Attempt).filter(
        Attempt.challenge_id == challenge_id,
        Attempt.status == AttemptStatus.SUBMITTED
    ).all()

    performance = defaultdict(lambda: {
        "total_score": Decimal("0"),
        "submitted_days": 0,
        "total_hints": 0
    })

    for attempt in attempts:
        pid = attempt.participant_id
        performance[pid]["total_score"] += Decimal(attempt.final_score or 0)
        performance[pid]["submitted_days"] += 1
        performance[pid]["total_hints"] += attempt.hints_used_count

    eligible = []

    for participant in participants:
        pid = participant.id
        data = performance.get(pid)

        if not data or data["submitted_days"] == 0:
            continue

        eligible.append({
            "participant_id": pid,
            "state": participant.state,
            "total_score": data["total_score"],
            "submitted_days": data["submitted_days"],
            "total_hints": data["total_hints"]
        })

    # ---------------- GLOBAL SORT ----------------

    eligible.sort(
        key=lambda x: (
            -x["total_score"],
            -x["submitted_days"],
            x["total_hints"],
            str(x["participant_id"])
        )
    )

    for index, participant in enumerate(eligible):
        participant["global_rank"] = index + 1

    total_ranked = len(eligible)

    # ---------------- STATE RANKS ----------------

    state_groups = defaultdict(list)

    for participant in eligible:
        state_groups[participant["state"]].append(participant)

    for state, group in state_groups.items():

        group.sort(
            key=lambda x: (
                -x["total_score"],
                -x["submitted_days"],
                x["total_hints"],
                str(x["participant_id"])
            )
        )

        for index, participant in enumerate(group):
            participant["state_rank"] = index + 1

    # ---------------- CLEAR OLD SNAPSHOT ----------------

    db.query(Ranking).filter(
        Ranking.challenge_id == challenge_id
    ).delete()

    db.commit()

    # ---------------- INSERT SNAPSHOT ----------------

    for participant in eligible:

        if total_ranked == 1:
            percentile = Decimal("100")
        else:
            percentile = (
                Decimal("100")
                - (
                    Decimal(participant["global_rank"] - 1)
                    / Decimal(total_ranked - 1)
                ) * Decimal("100")
            )

        ranking_row = Ranking(
            challenge_id=challenge_id,
            participant_id=participant["participant_id"],
            total_score=participant["total_score"],
            percentile=percentile,
            global_rank=participant["global_rank"],
            state_rank=participant["state_rank"],
            ranking_finalized=True
        )

        db.add(ranking_row)

    db.commit()

    return {
        "message": "Ranking finalized successfully",
        "ranked_participants": total_ranked
    }
