import asyncio
import logging
import sys

from sqlalchemy.future import select

from app.core.redis import RedisQueue
from app.db.database import SessionLocal
from app.models.evaluation import Evaluation

# Set up logging to stdout for container output visibility
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("worker")

# Define the Redis queue to match the API trigger publishing queue
evaluation_queue = RedisQueue("evaluation_jobs")


async def process_job(session_id_str: str) -> None:
    """Process a single evaluation job from the queue.

    Steps:
    1. Parse session_id.
    2. Simulate processing delay of 5 seconds (as required).
    3. Update the database Evaluation records for this session from 'Pending' to 'Completed'.
    """
    try:
        session_id = int(session_id_str)
        logger.info(f"Received evaluation job for session {session_id}. Starting processing...")

        # Simulate heavy work/processing delay (no LLM, as requested)
        await asyncio.sleep(5)

        # Update the database record using a dedicated database session block
        async with SessionLocal() as db:
            result = await db.execute(
                select(Evaluation).where(
                    Evaluation.session_id == session_id,
                    Evaluation.status == "Pending",
                )
            )
            evals = result.scalars().all()

            if not evals:
                logger.warning(f"No pending evaluations found for session {session_id}.")
                return

            for eval_record in evals:
                eval_record.status = "Completed"
                db.add(eval_record)

            await db.commit()
            logger.info(f"Successfully processed session {session_id}. Status set to 'Completed'.")

    except ValueError:
        logger.error(f"Invalid job payload (non-integer session_id): '{session_id_str}'")
    except Exception as e:
        logger.error(f"Error processing evaluation job for session {session_id_str}: {e}")


async def main() -> None:
    """Worker entry point. Listens to the Redis queue indefinitely."""
    logger.info("Starting Redis background worker. Listening for jobs...")
    while True:
        try:
            # Blocking pop (wait indefinitely until a job arrives)
            job = await evaluation_queue.dequeue(timeout=0)
            if job:
                await process_job(job)
        except Exception as e:
            logger.error(f"Worker queue listening error: {e}")
            await asyncio.sleep(2)  # Avoid tight loop in case of Redis connection loss


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker process stopped by user.")
        sys.exit(0)
