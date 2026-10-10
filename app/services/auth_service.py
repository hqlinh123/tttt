from datetime import timedelta
import random
import re
from uuid import UUID

from fastapi import HTTPException, status

from app.core import firebase
from app.domain.schemas.auth import (
    LoginRequest,
    SignupRequest,
    AuthResponse,
    SocialLoginRequest,
)
from app.core.security import (
    decode_reset_token,
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.helpers.errors_response import error_response
from app.helpers.success_response import success_response
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.token_repository import TokenRepository
from app.core.config.settings import settings
from app.services.email_service import EmailService
import random

def generate_otp(length: int = 6) -> str:
    return f"{random.randint(0, 10**length - 1):0{length}d}"
def validate_email(email: str) -> str:
    email = email.strip().lower()

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise ValueError("Invalid email format")
    return email
class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: TokenRepository,
        email_service: EmailService | None = None,
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.email_service = email_service

    # ---------------- LOGIN ----------------
    async def login(self, payload: LoginRequest):
        user = await self.user_repo.get_by_email(payload.email)

        if not user or not verify_password(payload.password, user.password_hash):
            error_response(
                message="Invalid email or password",
                code="AUTH_INVALID_CREDENTIALS",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        tokens = await self._generate_tokens(user.id)

        if not user.email_verified:
            otp = generate_otp()
            await self.token_repo.save_otp(user.id, otp)

            if self.email_service:
                await self.email_service.send_otp(user.email, otp)

        return success_response(
            message="Login successful",
            data={
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
                "expires_in": tokens.expires_in,
                "is_email_verified": user.email_verified,
                 "id": str(user.id),
                "email": user.email,
                "name": getattr(user, "name", None),
            }
        )

    # ---------------- SIGNUP ----------------
    async def signup(self, payload: SignupRequest):
        email = validate_email(payload.email) 
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Signup failed",
                    "errors": {
                        "email": "Email already exists"
                    },
                },
            )

        user = await self.user_repo.create(
            email=email,
            password_hash=hash_password(payload.password),
            name=payload.name,
            email_verified=False,
        )

        otp = generate_otp()
        await self.token_repo.save_otp(user.id, otp)

        if self.email_service:
            await self.email_service.send_otp(user.email, otp)

        return {
            "success": True,
            "message": "OTP sent to your email",
            "data": {
                "email": user.email
            }
        }
    # ---------------- SOCIAL LOGIN ----------------
    async def social_login(
        self, payload: SocialLoginRequest
    ) -> AuthResponse:

        if not payload.firebase_id_token:
            raise ValueError("firebase_id_token is required")

        # 1. Verify Firebase token
        try:
            decoded_token = firebase.verify_firebase_token(
                payload.firebase_id_token
            )
        except Exception:
            raise ValueError("Invalid Firebase token")

        social_uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        name = decoded_token.get("name")

        firebase_info = decoded_token.get("firebase", {})
        provider_raw = firebase_info.get("sign_in_provider")

        if not social_uid or not provider_raw:
            raise ValueError("Invalid token payload")

        provider_map = {
            "google.com": "google",
            "apple.com": "apple",
            "facebook.com": "facebook",
        }
        provider = provider_map.get(provider_raw, provider_raw)

        # 2. Find user
        user = await self.user_repo.get_by_social_uid(
            social_uid=social_uid,
        )

        if not user and email:
            user = await self.user_repo.get_by_email(email)

        # 3. Create or link
        if not user:
            user = await self.user_repo.create(
                email=email,
                name=name,
                social_uid=social_uid,
                provider=provider,
            )
        else:
            if not getattr(user, "social_uid", None):
                await self.user_repo.update_social(
                    user.id,
                    social_uid=social_uid,
                    provider=provider,
                )

            tokens = await self._generate_tokens(user.id)

            social_data = AuthResponse(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                expires_in=tokens.expires_in,
                email=user.email,
                name=getattr(user, "name", None),
            )

            return success_response(
                message="Login successful",
                data=social_data
            )

        return 

    # ---------------- REFRESH TOKEN ----------------
    async def refresh_token(
        self, refresh_token: str
    ) -> AuthResponse:
        payload = decode_refresh_token(refresh_token)
        user_id = payload.get("sub")

        if not user_id:
            raise ValueError("Invalid refresh token")

        if not await self.token_repo.is_valid(refresh_token):
            raise ValueError("Refresh token revoked")

        await self.token_repo.revoke(refresh_token)

        new_refresh_token = create_refresh_token(subject=user_id)
        await self.token_repo.save_refresh_token(
            user_id=user_id,
            refresh_token=new_refresh_token,
        )

        access_token = create_access_token(
            subject=user_id,
            expires_delta=timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            ),
        )

        return AuthResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ---------------- LOGOUT ----------------
    async def logout(self, refresh_token: str | None):
        if refresh_token:
            await self.token_repo.revoke(refresh_token)

    # ---------------- FORGOT PASSWORD ----------------
    async def forgot_password(self, email: str):
        user = await self.user_repo.get_by_email(email)

        # do NOT reveal user existence
        if not user:
            return {"message": "If email exists, instructions sent"}

        otp_count = await self.token_repo.count_recent_otp(user.id)

        if otp_count >= 3:
            reset_token = create_access_token(
                subject=str(user.id),
                expires_delta=timedelta(minutes=15),
                extra_claims={"type": "reset"},  # ✅ FIX
            )

            await self.token_repo.save_reset_token(
                user_id=user.id,
                token=reset_token,
            )

            if self.email_service:
                await self.email_service.send_reset_link(
                    user.email, reset_token
                )

            return {"message": "Reset link sent"}

        otp = generate_otp()

        await self.token_repo.save_otp(user.id, otp)

        if self.email_service:
            await self.email_service.send_otp(user.email, otp)

        return {"message": "OTP sent"}
    # ---------------- RESET PASSWORD ----------------
    async def reset_password(self, token: str, new_password: str):
        try:
            payload = decode_reset_token(token)
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid token",
            )

        user_id = payload.get("sub")
        token_type = payload.get("type")

        if not user_id or token_type != "reset":
            raise HTTPException(
                status_code=400,
                detail="Invalid token payload",
            )

        is_valid = await self.token_repo.is_valid(token, "reset")
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail="Token expired or revoked",
            )

        if len(new_password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 6 characters",
            )

        # ✅ optional: prevent reuse
        user = await self.user_repo.get_by_id(int(user_id))
        if verify_password(new_password, user.password_hash):
            raise HTTPException(
                status_code=400,
                detail="New password must be different",
            )

        await self.user_repo.update_password(
            user_id=int(user_id),
            password_hash=hash_password(new_password),
        )

        # ✅ revoke token (one-time use)
        await self.token_repo.revoke(token)

        return {"message": "Password reset successfully"}
    # ---------------- PRIVATE ----------------
    async def _generate_tokens(self, user_id: UUID) -> AuthResponse:
        access_token = create_access_token(
            subject=user_id,
            expires_delta=timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            ),
        )

        refresh_token = create_refresh_token(subject=user_id)

        await self.token_repo.save_refresh_token(
            user_id=user_id,
            refresh_token=refresh_token,
        )

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
   
    async def verify_otp(self, email: str, otp: str):
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=400,
                detail="Invalid OTP",
            )

        valid = await self.token_repo.verify_otp(user.id, otp)
        if not valid:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired OTP",
            )

        # ✅ include token type
        reset_token = create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=10),
            extra_claims={"type": "reset"},
        )

        await self.token_repo.save_reset_token(
            user_id=user.id,
            token=reset_token,
        )

        return {"reset_token": reset_token}
    
    async def verify_signup_otp(self, email: str, otp: str):
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(400, "Invalid request")

        valid = await self.token_repo.verify_otp(user.id, otp)
        if not valid:
            raise error_response(
                message="Invalid or expired OTP",
                code="AUTH_INVALID_OTP",
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        await self.user_repo.mark_email_verified(user.id)
        tokens = await self._generate_tokens(user.id)
        return success_response(
        message="Email verified successfully",
        data={
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "expires_in": tokens.expires_in,
            "id": str(user.id),
            "email": user.email,
            "name": getattr(user, "name", None),
            "is_email_verified": True,
        }
    )
    
        # ---------------- RESEND OTP ----------------
    async def resend_otp(self, email: str):
        email = validate_email(email)

        user = await self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found",
            )

        if user.email_verified:
            return success_response(
                message="Email already verified",
                data={"email": user.email, "is_email_verified": True}
            )
        otp_count = await self.token_repo.count_recent_otp(user.id)

        if otp_count >= 5:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many OTP requests. Please try again later.",
            )

        otp = generate_otp()

        await self.token_repo.save_otp(user.id, otp)

        if self.email_service:
            await self.email_service.send_otp(user.email, otp)

        return success_response(
            message="OTP resent successfully",
            data={"email": user.email}
        )
    # ---------------- GET PROFILE ----------------
    async def get_profile(self, user_id: UUID):
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return success_response(
            message="Get profile successfully",
            data={
                "id": str(user.id),
                "email": user.email,
                "name": getattr(user, "name", None),
                "is_email_verified": user.email_verified,
            }
        )