from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    """Schema for validating user registration request data."""

    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1)
    role: str = Field(..., description="Role must be 'admin', 'teacher', 'parent', or 'student'")

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        allowed_roles = {"admin", "teacher", "parent", "student"}
        if value not in allowed_roles:
            raise ValueError(f"Role must be one of {allowed_roles}")
        return value


class UserResponse(BaseModel):
    """Schema for serializing user response data."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    role: str
