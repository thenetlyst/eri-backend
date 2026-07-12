import csv
import io
import uuid

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.user import User
from app.models.participant import Participant


router = APIRouter(prefix="/admin", tags=["Admin"])


REQUIRED_COLUMNS = {
    "name",
    "email",
    "participant_code",
    "college",
    "graduation_year",
    "account_status",
    "state",
}


@router.post("/upload-participants")
async def upload_participants(
    file: UploadFile = File(...),
    challenge_id: str = None,
    db: Session = Depends(get_db),
):
    if not challenge_id:
        raise HTTPException(status_code=400, detail="challenge_id is required")

    contents = await file.read()
    csv_text = contents.decode("utf-8")
    reader = csv.DictReader(io.StringIO(csv_text))

    # 🔍 Validate columns
    missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {missing}",
        )

    created_users = 0
    created_participants = 0
    skipped = 0

    for row in reader:
        email = row["email"].strip().lower()
        participant_code = row["participant_code"].strip()

        # 🔹 1. Get or create user
        user = db.query(User).filter(User.email == email).first()

        if not user:
            user = User(
                id=uuid.uuid4(),
                email=email,
                participant_code=participant_code,
                name=row["name"].strip(),
            )
            db.add(user)
            db.flush()
            created_users += 1

        # 🔹 2. Check if participant exists
        existing = (
            db.query(Participant)
            .filter(
                Participant.user_id == user.id,
                Participant.challenge_id == challenge_id,
            )
            .first()
        )

        if existing:
            skipped += 1
            continue

        # 🔹 3. Create participant
        participant = Participant(
            id=uuid.uuid4(),
            user_id=user.id,
            challenge_id=challenge_id,
            state=row["state"].strip(),
            college=row["college"].strip(),
            account_status=row["account_status"].strip(),
            name=row["name"].strip(),
            graduation_year=row["graduation_year"].strip(),
        )

        db.add(participant)
        created_participants += 1

    db.commit()

    return {
        "created_users": created_users,
        "created_participants": created_participants,
        "skipped": skipped,
    }