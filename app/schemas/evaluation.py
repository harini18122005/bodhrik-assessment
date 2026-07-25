from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EvaluationCreate(BaseModel):
    """Schema for validating evaluation trigger request data."""

    session_id: int


class EvaluationResponse(BaseModel):
    """Schema for serializing evaluation job states."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    status: str
    created_at: datetime
