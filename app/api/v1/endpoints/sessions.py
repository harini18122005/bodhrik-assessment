from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api.deps import RoleChecker, check_session_access, get_current_user, get_db
from app.models.parent_student import ParentStudent
from app.models.session import Session
from app.models.user import User
from app.schemas.session import SessionCreate, SessionResponse, SessionUpdate

router = APIRouter()


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_in: SessionCreate,
    current_user: User = Depends(RoleChecker(["admin", "teacher"])),
    db: AsyncSession = Depends(get_db),
) -> Session:
    """Create a new academic session.

    - Teachers can only create sessions where they are the teacher.
    - Admins can create sessions for any teacher.
    """
    # Teachers can only schedule sessions for themselves
    if current_user.role == "teacher" and session_in.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teachers can only schedule sessions for themselves.",
        )

    # Validate that the designated teacher exists and has the 'teacher' role
    teacher_res = await db.execute(select(User).where(User.id == session_in.teacher_id))
    teacher = teacher_res.scalars().first()
    if not teacher or teacher.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid teacher_id must be provided.",
        )

    # Validate that the designated student exists and has the 'student' role
    student_res = await db.execute(select(User).where(User.id == session_in.student_id))
    student = student_res.scalars().first()
    if not student or student.role != "student":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid student_id must be provided.",
        )

    db_session = Session(
        title=session_in.title,
        description=session_in.description,
        date=session_in.date,
        teacher_id=session_in.teacher_id,
        student_id=session_in.student_id,
    )
    db.add(db_session)
    await db.commit()

    # Reload relationships for JSON serialization
    result = await db.execute(
        select(Session)
        .options(selectinload(Session.teacher), selectinload(Session.student))
        .where(Session.id == db_session.id)
    )
    return result.scalars().first()


@router.get("/", response_model=list[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Session]:
    """Retrieve all sessions visible to the current user.

    - Admin: Sees all sessions in the system.
    - Teacher: Sees sessions they are teaching.
    - Student: Sees sessions they are attending.
    - Parent: Sees sessions belonging to their children.
    """
    query = select(Session).options(selectinload(Session.teacher), selectinload(Session.student))

    if current_user.role == "admin":
        pass
    elif current_user.role == "teacher":
        query = query.where(Session.teacher_id == current_user.id)
    elif current_user.role == "student":
        query = query.where(Session.student_id == current_user.id)
    elif current_user.role == "parent":
        # Get children mapped to parent
        child_query = select(ParentStudent.student_id).where(
            ParentStudent.parent_id == current_user.id
        )
        child_res = await db.execute(child_query)
        child_ids = child_res.scalars().all()
        query = query.where(Session.student_id.in_(child_ids))
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid role.",
        )

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session: Session = Depends(check_session_access),
    db: AsyncSession = Depends(get_db),
) -> Session:
    """Retrieve a single session details by ID, verifying read permissions."""
    # Reload session relationships
    result = await db.execute(
        select(Session)
        .options(selectinload(Session.teacher), selectinload(Session.student))
        .where(Session.id == session.id)
    )
    return result.scalars().first()


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_in: SessionUpdate,
    session: Session = Depends(check_session_access),
    current_user: User = Depends(RoleChecker(["admin", "teacher"])),
    db: AsyncSession = Depends(get_db),
) -> Session:
    """Update a session by ID.

    - Teachers cannot reassign the session's teacher.
    - Validate that updated teacher/student IDs exist and have valid roles.
    """
    if current_user.role == "teacher":
        if session_in.teacher_id is not None and session_in.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teachers cannot reassign sessions to other teachers.",
            )

    if session_in.teacher_id is not None:
        teacher_res = await db.execute(select(User).where(User.id == session_in.teacher_id))
        teacher = teacher_res.scalars().first()
        if not teacher or teacher.role != "teacher":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valid teacher_id must be provided.",
            )
        session.teacher_id = session_in.teacher_id

    if session_in.student_id is not None:
        student_res = await db.execute(select(User).where(User.id == session_in.student_id))
        student = student_res.scalars().first()
        if not student or student.role != "student":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Valid student_id must be provided.",
            )
        session.student_id = session_in.student_id

    if session_in.title is not None:
        session.title = session_in.title
    if session_in.description is not None:
        session.description = session_in.description
    if session_in.date is not None:
        session.date = session_in.date

    db.add(session)
    await db.commit()

    result = await db.execute(
        select(Session)
        .options(selectinload(Session.teacher), selectinload(Session.student))
        .where(Session.id == session.id)
    )
    return result.scalars().first()


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session: Session = Depends(check_session_access),
    current_user: User = Depends(RoleChecker(["admin", "teacher"])),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a session by ID."""
    await db.delete(session)
    await db.commit()
    return None
