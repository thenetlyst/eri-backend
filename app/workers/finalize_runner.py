import asyncio
from app.workers.finalize_worker import finalize_expired_attempts_loop

if __name__ == "__main__":
    asyncio.run(finalize_expired_attempts_loop())