from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RoleChecker, check_session_access, get_db
from app.core.redis import RedisQueue
from app.models.evaluation import Evaluation
from app.models.session import Session
from app.models.user import User
from app.schemas.evaluation import EvaluationResponse

router = APIRouter()

# Declare the Redis queue instance for evaluations
evaluation_queue = RedisQueue("evaluation_jobs")


@router.post(
    "/trigger/{session_id}", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED
)
async def trigger_evaluation(
    session: Session = Depends(check_session_access),
    current_user: User = Depends(RoleChecker(["admin", "teacher"])),
    db: AsyncSession = Depends(get_db),
) -> Evaluation:
    """Trigger an evaluation background job for a valid academic session.

    Execution sequence:
    1. check_session_access retrieves the session and verifies user permissions.
    2. Create a database evaluation entry initialized to 'Pending'.
    3. Publish the session_id into the Redis 'evaluation_jobs' FIFO queue.
    4. Return the evaluation metadata payload.
    """
    db_evaluation = Evaluation(
        session_id=session.id,
        status="Pending",
    )
    db.add(db_evaluation)
    await db.commit()
    await db.refresh(db_evaluation)

    # Enqueue session ID into Redis queue for background execution
    await evaluation_queue.enqueue(str(session.id))

    return db_evaluation
