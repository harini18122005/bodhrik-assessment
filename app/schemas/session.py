from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserResponse


class SessionCreate(BaseModel):
    """Schema for validating session creation request data."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    date: datetime
    teacher_id: int
    student_id: int


class SessionUpdate(BaseModel):
    """Schema for validating session modification request data."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)
    date: datetime | None = None
    teacher_id: int | None = None
    student_id: int | None = None


class SessionResponse(BaseModel):
    """Schema for serializing session response data, including related user models."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    date: datetime
    teacher_id: int
    student_id: int
    teacher: UserResponse
    student: UserResponse
