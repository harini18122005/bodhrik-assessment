from fastapi import Depends, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.db.session import get_db
from app.models.parent_student import ParentStudent
from app.models.session import Session
from app.models.user import User

# Define the OAuth2 security scheme for bearer token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """Authenticate and retrieve the active user using the provided JWT access token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the token payload
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError as err:
        raise credentials_exception from err

    # Query the user by email in the database
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception

    return user


class RoleChecker:
    """Reusable dependency to verify that the current user has one of the allowed roles."""

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """Evaluate if the user's role belongs to the allowed subset."""
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
        return current_user


async def check_session_access(
    session_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Session:
    """Reusable dependency that retrieves a session and checks if the current user has access to it.

    Access Rules:
    - Admin: Can access all sessions.
    - Teacher: Can only access sessions where teacher_id matches their user ID.
    - Parent: Can only access sessions belonging to their child (mapped in parent_students table).
    - Student: Can only access sessions where student_id matches their user ID.
    """
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # 1. Admins have unrestricted access
    if current_user.role == "admin":
        return session

    # 2. Teachers can only view/modify sessions they teach
    if current_user.role == "teacher":
        if session.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teachers can only access their own sessions.",
            )
        return session

    # 3. Parents can only view sessions of children mapped to them
    if current_user.role == "parent":
        assoc_result = await db.execute(
            select(ParentStudent).where(
                ParentStudent.parent_id == current_user.id,
                ParentStudent.student_id == session.student_id,
            )
        )
        mapping = assoc_result.scalars().first()
        if not mapping:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Parents can only access sessions belonging to their own child.",
            )
        return session

    # 4. Students can only view their own sessions
    if current_user.role == "student":
        if session.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students can only access their own sessions.",
            )
        return session

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access this resource.",
    )
