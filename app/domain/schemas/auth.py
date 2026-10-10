import re
from uuid import UUID
from enum import Enum
from typing import Optional, Dict, Any

from pydantic import (
    BaseModel,
    EmailStr,
    field_validator,
    model_validator,
)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SocialProvider(str, Enum):
    GOOGLE = "google"
    FACEBOOK = "facebook"
    APPLE = "apple"


class SocialLoginRequest(BaseModel):
    firebase_id_token: str
    device_info: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def validate_required_fields(self):
        if not self.firebase_id_token:
            raise ValueError(
                "firebase_id_token is required"
            )

        return self


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str):
        if len(v.encode("utf-8")) > 72:
            raise ValueError(
                "Password must be at most 72 bytes"
            )

        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: EmailStr):
        email = str(v).strip().lower()

        if not re.match(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            email,
        ):
            raise ValueError("Invalid email format")

        return email

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str):
        v = v.strip()

        if len(v) < 2:
            raise ValueError("Name too short")

        return v


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

    email: Optional[str] = None
    name: Optional[str] = None
    is_email_verified: Optional[bool] = None

    # Python UUID for Pydantic validation
    user_id: Optional[UUID] = None


class UserProfileResponse(BaseModel):
    id: UUID
    email: str
    name: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str


class EmailRequest(BaseModel):
    email: EmailStr