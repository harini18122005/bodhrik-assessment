from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserResponse


class SessionCreate(BaseModel):
    """Schema for validating session creation request data."""

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    date: datetime
    teacher_id: int
    student_id: int


class SessionUpdate(BaseModel):
    """Schema for validating session modification request data."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    date: Optional[datetime] = None
    teacher_id: Optional[int] = None
    student_id: Optional[int] = None


class SessionResponse(BaseModel):
    """Schema for serializing session response data, including related user models."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    date: datetime
    teacher_id: int
    student_id: int
    teacher: UserResponse
    student: UserResponse
