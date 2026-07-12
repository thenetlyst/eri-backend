from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from uuid import UUID
import asyncio
import logging

from app.db.session import SessionLocal
from app.models.attempt import Attempt

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{attempt_id}/events")
async def attempt_events(request: Request, attempt_id: UUID):

    async def event_stream():
        last_status = None

        logger.info(f"SSE CONNECTED: {attempt_id}")

        try:
            while True:

                # Client disconnected
                if await request.is_disconnected():
                    logger.info(f"SSE DISCONNECTED: {attempt_id}")
                    break

                with SessionLocal() as db:
                    attempt = (
                        db.query(Attempt)
                        .filter(Attempt.id == attempt_id)
                        .first()
                    )

                    if attempt:
                        current_status = attempt.status.value

                        # Send immediately
                        if last_status is None:
                            last_status = current_status
                            yield f"data: {current_status}\n\n"

                        # Send only on change
                        elif current_status != last_status:
                            last_status = current_status
                            yield f"data: {current_status}\n\n"

                # Keep connection alive
                yield ": ping\n\n"

                await asyncio.sleep(1)

        finally:
            logger.info(f"SSE CLOSED: {attempt_id}")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )